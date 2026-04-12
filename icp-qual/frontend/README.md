# ICP Qualification Frontend

Next.js 16 frontend for the ICP qualification flow and pipeline run monitor.

## Local development

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Runtime architecture

- App framework: Next.js 16 / React 19
- Runtime target: Cloud Run
- Image build: Docker multi-stage build with Next.js `standalone` output
- Auth: password gate via `src/middleware.ts`
- Backend integration: frontend API routes proxy to the Python pipeline backend with `PIPELINE_BACKEND_URL`

## Production URLs

- `https://demoupscale.com` → existing `upscale-reports` service
- `https://demoupscale.com/icp` → this frontend (`upscale-icp-frontend`)
- Direct Cloud Run URL: `https://upscale-icp-frontend-ghy5squ27q-uc.a.run.app/icp`

## Infrastructure configuration

### Cloud Run services

- `upscale-reports`: existing root-site service
- `upscale-icp-frontend`: standalone Next.js service for the ICP app

### Path routing

The frontend is deployed under the `/icp` path prefix.

- `next.config.ts` sets `basePath: "/icp"`
- The global HTTP(S) load balancer routes:
  - `/` → `backend-upscale-reports`
  - `/icp` and `/icp/*` → `backend-icp-frontend`

### Google Cloud resources

- Global static IP: `34.49.156.96`
- Managed certificate in front of `demoupscale.com`
- Serverless NEGs:
  - `neg-upscale-reports`
  - `neg-icp-frontend`
- Backend services:
  - `backend-upscale-reports`
  - `backend-icp-frontend`
- URL map: `demoupscale-url-map`

### DNS

Cloud DNS zone: `demoupscale`

Current public records:

- `demoupscale.com A 34.49.156.96`
- `www.demoupscale.com A 34.49.156.96`

## Environment variables

- `PIPELINE_BACKEND_URL`: Python API base URL for `/api/pipeline/*` and `/api/reports`
- `SITE_PASSWORD`: password used by the middleware login gate
- `NODE_ENV=production`: production runtime mode

## Deploying

Use `deploy.sh` to build and deploy the frontend service:

```bash
PIPELINE_BACKEND_URL=https://your-backend.run.app \
SITE_PASSWORD=your-password \
./deploy.sh
```

The script:

1. Builds and pushes the image to Artifact Registry
2. Deploys `upscale-icp-frontend` to Cloud Run
3. Prints the service URL and reminders for load balancer path routing

## Important implementation detail

Because the app is mounted under `/icp`, the middleware login page must submit to `/icp/api/auth` rather than `/api/auth`. That path is hard-coded inside the inline login HTML in `src/middleware.ts`.
