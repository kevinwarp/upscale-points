#!/bin/bash

# Company Pulse - GCP Setup Script
# This script sets up the GCP project, enables APIs, and configures secrets

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Company Pulse - GCP Setup${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Prompt for project ID
read -p "Enter your GCP Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Project ID is required${NC}"
    exit 1
fi

echo -e "${YELLOW}Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Set region
REGION="us-central1"
echo -e "${YELLOW}Setting default region to: $REGION${NC}"
gcloud config set run/region $REGION

echo ""
echo -e "${GREEN}📦 Enabling required APIs...${NC}"

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudresourcemanager.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"

echo ""
echo -e "${GREEN}🔐 Setting up secrets in Secret Manager...${NC}"
echo "You'll be prompted to enter each secret value."
echo ""

# Function to create secret
create_secret() {
    local SECRET_NAME=$1
    local SECRET_LABEL=$2
    
    echo -e "${YELLOW}Creating secret: $SECRET_NAME${NC}"
    
    # Check if secret already exists
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        echo -e "${YELLOW}⚠️  Secret $SECRET_NAME already exists. Skipping...${NC}"
        return
    fi
    
    read -sp "Enter $SECRET_LABEL: " SECRET_VALUE
    echo ""
    
    if [ -z "$SECRET_VALUE" ]; then
        echo -e "${YELLOW}⚠️  Skipping empty value for $SECRET_NAME${NC}"
        return
    fi
    
    echo "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME \
        --data-file=- \
        --replication-policy="automatic" \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}✅ Created secret: $SECRET_NAME${NC}"
}

# Create secrets
create_secret "CLIENT_ID" "Day AI OAuth Client ID"
create_secret "CLIENT_SECRET" "Day AI OAuth Client Secret"
create_secret "REFRESH_TOKEN" "Day AI OAuth Refresh Token"
create_secret "HUBSPOT_ACCESS_TOKEN" "HubSpot Access Token"
create_secret "INSTANTLY_API_KEY" "Instantly API Key"
create_secret "BEEHIIV_API_KEY" "Beehiiv API Key"
create_secret "STORELEADS_API_KEY" "StoreLeads API Key"
create_secret "GOOGLE_CLIENT_ID" "Google OAuth Client ID"
create_secret "GOOGLE_CLIENT_SECRET" "Google OAuth Client Secret"
create_secret "NEXTAUTH_SECRET" "NextAuth Secret (random string, e.g. run: openssl rand -base64 32)"

echo -e "${YELLOW}⚠️  NEXTAUTH_URL will be set after first deploy (requires the Cloud Run service URL)${NC}"

echo ""
echo -e "${GREEN}👤 Creating service account for Cloud Run...${NC}"

SERVICE_ACCOUNT="company-pulse-runner"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠️  Service account already exists. Skipping creation...${NC}"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT \
        --display-name="Company Pulse Cloud Run Service Account" \
        --project=$PROJECT_ID
    echo -e "${GREEN}✅ Service account created${NC}"
fi

echo ""
echo -e "${GREEN}🔑 Granting Secret Manager access to service account...${NC}"

# Grant Secret Accessor role for each secret
for SECRET_NAME in CLIENT_ID CLIENT_SECRET REFRESH_TOKEN HUBSPOT_ACCESS_TOKEN INSTANTLY_API_KEY BEEHIIV_API_KEY STORELEADS_API_KEY GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET NEXTAUTH_SECRET; do
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        gcloud secrets add-iam-policy-binding $SECRET_NAME \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="roles/secretmanager.secretAccessor" \
            --project=$PROJECT_ID \
            --quiet
    fi
done

echo -e "${GREEN}✅ Permissions granted${NC}"

echo ""
echo -e "${GREEN}✅ GCP Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Build and test Docker image locally:"
echo "   ${YELLOW}docker build -t company-pulse .${NC}"
echo ""
echo "2. Deploy to Cloud Run:"
echo "   ${YELLOW}./scripts/deploy.sh${NC}"
echo ""
echo "3. Or set up automated deployments with Cloud Build:"
echo "   ${YELLOW}gcloud builds submit --config cloudbuild.yaml${NC}"
