#!/usr/bin/env pwsh
# ============================================================
# EcoTrack — GCP Setup & Cloud Run Deploy Script (PowerShell)
# Run this AFTER: gcloud auth login && gcloud config set project YOUR_PROJECT_ID
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$true)]
    [string]$DatabaseUrl,

    [Parameter(Mandatory=$true)]
    [string]$DjangoSecretKey,

    [string]$Region = "asia-south1",
    [string]$BackendService = "ecotrack-backend",
    [string]$FrontendService = "ecotrack-frontend",
    [string]$Registry = "ecotrack"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  EcoTrack — Google Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project  : $ProjectId" -ForegroundColor Yellow
Write-Host "Region   : $Region" -ForegroundColor Yellow
Write-Host "Backend  : $BackendService" -ForegroundColor Yellow
Write-Host "Frontend : $FrontendService" -ForegroundColor Yellow
Write-Host ""

# ---- 1. Set active project ----
Write-Host "► Setting active GCP project..." -ForegroundColor Green
gcloud config set project $ProjectId

# ---- 2. Enable required APIs ----
Write-Host "► Enabling GCP APIs (this takes ~2 min first time)..." -ForegroundColor Green
$apis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com"
)
foreach ($api in $apis) {
    Write-Host "   Enabling $api"
    gcloud services enable $api --quiet
}

# ---- 3. Create Artifact Registry repo ----
Write-Host "► Creating Artifact Registry repository '$Registry'..." -ForegroundColor Green
gcloud artifacts repositories create $Registry `
    --repository-format=docker `
    --location=$Region `
    --description="EcoTrack container images" `
    --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   (Repository already exists — continuing)" -ForegroundColor Yellow
}

$RegistryHost = "$Region-docker.pkg.dev"
$ImageBase = "$RegistryHost/$ProjectId/$Registry"

# ---- 4. Authenticate Docker ----
Write-Host "► Configuring Docker auth for Artifact Registry..." -ForegroundColor Green
gcloud auth configure-docker $RegistryHost --quiet

# ---- 5. Build & deploy backend via Cloud Build (no local Docker needed) ----
Write-Host ""
Write-Host "► Submitting BACKEND build to Cloud Build..." -ForegroundColor Green
$Tag = (Get-Date -Format "yyyyMMdd-HHmmss")
$BackendImage = "$ImageBase/backend:$Tag"

gcloud builds submit ./backend `
    --tag $BackendImage `
    --region $Region `
    --quiet

Write-Host "► Deploying backend to Cloud Run..." -ForegroundColor Green
gcloud run deploy $BackendService `
    --image $BackendImage `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --timeout 120 `
    --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.cloudrun" `
    --set-env-vars "DJANGO_SECRET_KEY=$DjangoSecretKey" `
    --set-env-vars "DATABASE_URL=$DatabaseUrl" `
    --set-env-vars "DJANGO_ALLOWED_HOSTS=*" `
    --set-env-vars "DJANGO_DEBUG=False" `
    --quiet

$BackendUrl = gcloud run services describe $BackendService `
    --region $Region `
    --format "value(status.url)"

Write-Host "✅ Backend live at: $BackendUrl" -ForegroundColor Green

# ---- 6. Run Django migrations ----
Write-Host ""
Write-Host "► Running Django migrations..." -ForegroundColor Green
gcloud run jobs create "ecotrack-migrate-$Tag" `
    --image $BackendImage `
    --region $Region `
    --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.cloudrun" `
    --set-env-vars "DJANGO_SECRET_KEY=$DjangoSecretKey" `
    --set-env-vars "DATABASE_URL=$DatabaseUrl" `
    --set-env-vars "DJANGO_ALLOWED_HOSTS=*" `
    --set-env-vars "DJANGO_DEBUG=False" `
    --command "python" `
    --args "manage.py,migrate,--noinput" `
    --execute-now `
    --wait `
    --quiet
Write-Host "✅ Migrations complete" -ForegroundColor Green

# ---- 7. Build & deploy frontend ----
Write-Host ""
Write-Host "► Submitting FRONTEND build to Cloud Build..." -ForegroundColor Green
$FrontendImage = "$ImageBase/frontend:$Tag"

gcloud builds submit ./frontend `
    --tag $FrontendImage `
    --region $Region `
    --substitutions "_VITE_API_BASE_URL=$BackendUrl" `
    --quiet

# Since Cloud Build doesn't pass build-args the same way, build locally with gcloud builds
# Alternative: use the cloudbuild.yaml for frontend
Write-Host "► Deploying frontend to Cloud Run..." -ForegroundColor Green
gcloud run deploy $FrontendService `
    --image $FrontendImage `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --memory 256Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5 `
    --quiet

$FrontendUrl = gcloud run services describe $FrontendService `
    --region $Region `
    --format "value(status.url)"

# ---- 8. Update backend CORS with frontend URL ----
Write-Host ""
Write-Host "► Updating backend CORS with frontend URL..." -ForegroundColor Green
gcloud run services update $BackendService `
    --region $Region `
    --update-env-vars "CORS_ALLOWED_ORIGINS=$FrontendUrl" `
    --quiet

# ---- Done ----
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Frontend (your app):  $FrontendUrl" -ForegroundColor White
Write-Host "⚙️  Backend API:          $BackendUrl/api/v1/" -ForegroundColor White
Write-Host "🔧 Django Admin:         $BackendUrl/admin/" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open $FrontendUrl in your browser"
Write-Host "  2. Create a superuser: gcloud run jobs create createsu ..."
Write-Host "  3. Add GitHub Actions secrets (see deploy-cloudrun.yml)"
Write-Host ""
