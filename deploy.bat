@echo off
setlocal EnableDelayedExpansion

set GCLOUD="C:\Users\SUDIPTO BHADRA\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set PROJECT_ID=election-guide-app
set REGION=asia-south1
set DJANGO_SECRET=WQ9bZrMN9oQdEuJZ7h4Llya4-QAZJlZc_Zh8wvdkkydrsZBaSgpixB4MuUhHNECmFTw

echo =============================================
echo  EcoTrack - Google Cloud Run Deployment
echo =============================================
echo.

echo [1/6] Setting active project to %PROJECT_ID% ...
%GCLOUD% config set project %PROJECT_ID%

echo.
echo [2/6] Enabling required APIs (takes ~2 min)...
echo [3/6] Enabling Cloud Run API...
%GCLOUD% services enable run.googleapis.com --quiet
if %ERRORLEVEL% neq 0 (
    echo ERROR: Could not enable APIs. Please ensure billing is enabled at:
    echo https://console.cloud.google.com/billing/linkedaccount?project=%PROJECT_ID%
    pause
    exit /b 1
)

echo [4/6] Enabling Cloud Build API...
%GCLOUD% services enable cloudbuild.googleapis.com --quiet

echo [5/6] Enabling Artifact Registry API...
%GCLOUD% services enable artifactregistry.googleapis.com --quiet

echo.
echo [5/6] Deploying BACKEND to Cloud Run (building in cloud - no Docker needed)...
echo This will take 5-8 minutes...
%GCLOUD% run deploy ecotrack-backend ^
    --source backend ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --port 8080 ^
    --memory 512Mi ^
    --cpu 1 ^
    --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.cloudrun" ^
    --set-env-vars "DJANGO_SECRET_KEY=%DJANGO_SECRET%" ^
    --set-env-vars "DJANGO_ALLOWED_HOSTS=*" ^
    --set-env-vars "DJANGO_DEBUG=False" ^
    --quiet

echo.
echo Getting backend URL...
for /f "tokens=*" %%i in ('%GCLOUD% run services describe ecotrack-backend --region %REGION% --format "value(status.url)" 2^>nul') do set BACKEND_URL=%%i
echo Backend URL: %BACKEND_URL%

echo.
echo [6/6] Deploying FRONTEND to Cloud Run...
echo This will take 3-5 minutes...
%GCLOUD% run deploy ecotrack-frontend ^
    --source frontend ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --port 8080 ^
    --memory 256Mi ^
    --cpu 1 ^
    --quiet

echo.
for /f "tokens=*" %%i in ('%GCLOUD% run services describe ecotrack-frontend --region %REGION% --format "value(status.url)" 2^>nul') do set FRONTEND_URL=%%i

echo =============================================
echo  DEPLOYMENT COMPLETE!
echo =============================================
echo.
echo Your EcoTrack app is live at:
echo.
echo  Frontend:    %FRONTEND_URL%
echo  Backend API: %BACKEND_URL%/api/v1/
echo  Admin:       %BACKEND_URL%/admin/
echo.
echo Next: Update CORS by running:
echo %GCLOUD% run services update ecotrack-backend --region %REGION% --update-env-vars "CORS_ALLOWED_ORIGINS=%FRONTEND_URL%"
echo.
pause
