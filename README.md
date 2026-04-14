# Upscale Score Engine

Internal scoring engine that qualifies brands on a 1-10 Upscale Score using revenue data, industry alignment, and brand recognition.

## Quick Start

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your StoreLeads API key and database URL

# Generate Prisma client
npm run db:generate

# Run database migrations
npm run db:migrate

# Start dev server
npm run dev
```

## Docker

```bash
docker compose up
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/score` | Score a domain |
| GET | `/api/v1/score/:domain` | Get stored score |
| GET | `/api/v1/scores` | List/filter scores |
| PATCH | `/api/v1/score/:domain/overrides` | Update overrides |
| POST | `/api/v1/scores/bulk` | Bulk upload CSV |
| GET | `/api/v1/scores/bulk/:jobId` | Bulk job status |
| GET | `/api/v1/scores/export` | Export CSV |
| GET | `/health` | Health check |

## Scoring

**Upscale Score = GMV Score (1-5) + Industry Score (1-3) + Recognition Score (0-2)**

| Tier | Score |
|------|-------|
| Tier 1 | 9-10 |
| Tier 2 | 7-8 |
| Tier 3 | 5-6 |
| Tier 4 | 3-4 |
| Tier 5 | 1-2 |

## Testing

```bash
npm test
```
