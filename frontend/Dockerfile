# Frontend Docker — two-stage build
# Stage 1: Build the React/Vite app
FROM node:20-slim AS builder

WORKDIR /app

# Copy dependency manifests first (layer cache)
COPY package*.json ./
RUN npm ci --prefer-offline

# Accept backend URL as build argument (injected by Cloud Build / GH Actions)
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy source and build
COPY . .
RUN npm run build

# -------------------------------------------------------
# Stage 2: Serve with Nginx (tiny alpine image)
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our SPA-aware nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files from Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

# Cloud Run uses port 8080 for HTTP
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
