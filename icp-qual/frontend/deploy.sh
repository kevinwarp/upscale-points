#!/usr/bin/env bash
# Deploy the ICP frontend to Cloud Run and route demoupscale.com/icp to it.
#
# Prerequisites:
#   - gcloud CLI authenticated (gcloud auth login)
#   - Project set:  gcloud config set project YOUR_PROJECT_ID
#   - Artifact Registry repo exists, or use --source for Cloud Build
#
# Usage:
#   PIPELINE_BACKEND_URL=https://your-backend.run.app \
#   SITE_PASSWORD=your-password \
#   ./deploy.sh

set -euo pipefail

PROJECT=$(gcloud config get-value project)
REGION="us-central1"
SERVICE="upscale-icp-frontend"
REPOSITORY="cloud-run-images"
IMAGE="us-central1-docker.pkg.dev/${PROJECT}/${REPOSITORY}/${SERVICE}:latest"

BACKEND_URL="${PIPELINE_BACKEND_URL:-http://localhost:8000}"
PASSWORD="${SITE_PASSWORD:-scalewithupscale}"

echo "→ Building and pushing image: ${IMAGE}"
gcloud builds submit \
  --tag "${IMAGE}" \
  .

echo "→ Deploying Cloud Run service: ${SERVICE}"
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "PIPELINE_BACKEND_URL=${BACKEND_URL},SITE_PASSWORD=${PASSWORD},NODE_ENV=production"

SERVICE_URL=$(gcloud run services describe "${SERVICE}" \
  --region "${REGION}" \
  --format "value(status.url)")

echo ""
echo "✓ Service deployed: ${SERVICE_URL}"
echo ""
echo "Current production routing:"
echo "  https://demoupscale.com      -> upscale-reports"
echo "  https://demoupscale.com/icp  -> upscale-icp-frontend"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NEXT STEP: Route demoupscale.com/icp → this service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option A — Google Cloud Load Balancer (recommended if you already have one)"
echo ""
echo "  1. Create a serverless NEG for this Cloud Run service:"
echo "     gcloud compute network-endpoint-groups create icp-frontend-neg \\"
echo "       --region=${REGION} \\"
echo "       --network-endpoint-type=serverless \\"
echo "       --cloud-run-service=${SERVICE}"
echo ""
echo "  2. Create a backend service pointing at the NEG:"
echo "     gcloud compute backend-services create icp-frontend-backend \\"
echo "       --load-balancing-scheme=EXTERNAL_MANAGED \\"
echo "       --global"
echo "     gcloud compute backend-services add-backend icp-frontend-backend \\"
echo "       --network-endpoint-group=icp-frontend-neg \\"
echo "       --network-endpoint-group-region=${REGION} \\"
echo "       --global"
echo ""
echo "  3. Add a path matcher to your existing URL map:"
echo "     gcloud compute url-maps import YOUR_URL_MAP --global << 'EOF'"
echo "     # Add under pathMatchers:"
echo "     - name: icp-path-matcher"
echo "       defaultService: YOUR_EXISTING_DEFAULT_BACKEND"
echo "       pathRules:"
echo "         - paths: ['/icp', '/icp/*']"
echo "           service: projects/${PROJECT}/global/backendServices/icp-frontend-backend"
echo "     EOF"
echo ""
echo "Option B — No existing Load Balancer (set up fresh mapping)"
echo ""
echo "  Use the GCP Console: Cloud Run → Manage Custom Domains → Map 'demoupscale.com'"
echo "  This creates a direct domain mapping (no path-based routing support)."
echo "  For path routing (/icp prefix), you need the Load Balancer approach above."
echo ""
echo "Service URL for testing before domain is wired up:"
echo "  ${SERVICE_URL}"
