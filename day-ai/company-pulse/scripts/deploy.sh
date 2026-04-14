#!/bin/bash

# Company Pulse - Manual Deployment Script
# Build Docker image locally and deploy to Cloud Run

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Company Pulse - Manual Deployment${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project configured${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${BLUE}📦 Project: $PROJECT_ID${NC}"

# Set variables
REGION="us-central1"
SERVICE_NAME="company-pulse"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo -e "${BLUE}🏷️  Tag: $TAG${NC}"
echo ""

# Confirm deployment
read -p "Deploy to Cloud Run? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Deployment cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Building Docker image...${NC}"

# Build from project directory (SDK tarball is bundled)
docker build \
    -t $IMAGE_NAME:$TAG \
    -t $IMAGE_NAME:latest \
    -f Dockerfile \
    .

echo -e "${GREEN}✅ Image built${NC}"

echo ""
echo -e "${GREEN}Step 2: Pushing image to Container Registry...${NC}"

# Configure docker for GCR
gcloud auth configure-docker --quiet

# Push images
docker push $IMAGE_NAME:$TAG
docker push $IMAGE_NAME:latest

echo -e "${GREEN}✅ Image pushed${NC}"

echo ""
echo -e "${GREEN}Step 3: Deploying to Cloud Run...${NC}"

# Check if NEXTAUTH_URL secret exists
NEXTAUTH_URL_EXISTS=$(gcloud secrets describe NEXTAUTH_URL --project=$PROJECT_ID &>/dev/null && echo "yes" || echo "no")

if [ "$NEXTAUTH_URL_EXISTS" = "yes" ]; then
    SECRETS="CLIENT_ID=CLIENT_ID:latest,CLIENT_SECRET=CLIENT_SECRET:latest,REFRESH_TOKEN=REFRESH_TOKEN:latest,HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest,BEEHIIV_API_KEY=BEEHIIV_API_KEY:latest,INSTANTLY_API_KEY=INSTANTLY_API_KEY:latest,STORELEADS_API_KEY=STORELEADS_API_KEY:latest,NEXTAUTH_SECRET=NEXTAUTH_SECRET:latest,NEXTAUTH_URL=NEXTAUTH_URL:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,API_KEY=API_KEY:latest"
else
    echo -e "${YELLOW}⚠️  NEXTAUTH_URL secret not found — deploying without it (first deploy)${NC}"
    SECRETS="CLIENT_ID=CLIENT_ID:latest,CLIENT_SECRET=CLIENT_SECRET:latest,REFRESH_TOKEN=REFRESH_TOKEN:latest,HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest,BEEHIIV_API_KEY=BEEHIIV_API_KEY:latest,INSTANTLY_API_KEY=INSTANTLY_API_KEY:latest,STORELEADS_API_KEY=STORELEADS_API_KEY:latest,NEXTAUTH_SECRET=NEXTAUTH_SECRET:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,API_KEY=API_KEY:latest"
fi

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:$TAG \
    --region $REGION \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 50 \
    --min-instances 0 \
    --max-instances 10 \
    --port 3000 \
    --allow-unauthenticated \
    --service-account company-pulse-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars NODE_ENV=production,DAY_AI_BASE_URL=https://day.ai,BEEHIIV_PUBLICATION_ID=pub_a7e962da-3337-4ba9-baca-68806e618eca \
    --set-secrets $SECRETS

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo -e "${GREEN}🌐 Service URL:${NC}"
echo -e "${BLUE}$SERVICE_URL${NC}"

if [ "$NEXTAUTH_URL_EXISTS" = "no" ]; then
    echo ""
    echo -e "${YELLOW}📋 Next steps for Google login to work:${NC}"
    echo -e "1. Create the NEXTAUTH_URL secret:"
    echo -e "   ${YELLOW}echo -n '$SERVICE_URL' | gcloud secrets create NEXTAUTH_URL --data-file=- --project=$PROJECT_ID${NC}"
    echo -e "2. Grant secret access to the service account:"
    echo -e "   ${YELLOW}gcloud secrets add-iam-policy-binding NEXTAUTH_URL --member=serviceAccount:company-pulse-runner@$PROJECT_ID.iam.gserviceaccount.com --role=roles/secretmanager.secretAccessor --project=$PROJECT_ID${NC}"
    echo -e "3. Add this redirect URI in Google Cloud Console OAuth credentials:"
    echo -e "   ${YELLOW}$SERVICE_URL/api/auth/callback/google${NC}"
    echo -e "4. Re-run ./scripts/deploy.sh to pick up NEXTAUTH_URL"
fi

echo ""
echo "Test the service:"
echo -e "${YELLOW}curl $SERVICE_URL/api/company-status?organization_id=lumedeodorant.com${NC}"
