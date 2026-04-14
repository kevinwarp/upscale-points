# Technical Requirements Document (TRD)

## Upscale Score Engine (with StoreLeads API Integration)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Admin UI    │────▶│  REST API Layer   │────▶│  Scoring Engine  │
│  (Frontend)  │◀────│  (Express/Node)   │◀────│  (Core Logic)    │
└──────────────┘     └────────┬─────────┘     └────────┬─────────┘
                              │                         │
                     ┌────────▼─────────┐     ┌────────▼─────────┐
                     │   PostgreSQL     │     │  StoreLeads API  │
                     │   (Data Store)   │     │  (External)      │
                     └──────────────────┘     └──────────────────┘
```

### 1.2 Tech Stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| Runtime      | Node.js (v20 LTS)                   |
| Framework    | Express.js                          |
| Language     | TypeScript                          |
| Database     | PostgreSQL 15+                      |
| ORM          | Prisma                              |
| API Docs     | Swagger / OpenAPI 3.0               |
| Testing      | Jest + Supertest                    |
| Admin UI     | React (Vite) + Tailwind CSS         |
| Deployment   | Docker / Docker Compose             |

---

## 2. API Design

### 2.1 Score a Domain

**POST** `/api/v1/score`

Request:
```json
{
  "domain": "jonesroadbeauty.com"
}
```

Response `200 OK`:
```json
{
  "id": "a1b2c3d4-...",
  "domain": "jonesroadbeauty.com",
  "estimated_monthly_sales": 13500000,
  "estimated_annual_gmv": 162000000,
  "gmv_score": 5,
  "industry": "Beauty",
  "industry_score": 3,
  "recognition_score": 0,
  "total_upscale_score": 8,
  "tier": "Tier 2",
  "flags": [],
  "created_at": "2026-02-28T12:00:00Z"
}
```

Error Response `502`:
```json
{
  "error": "STORELEADS_UNAVAILABLE",
  "message": "StoreLeads API unreachable after 3 retries",
  "domain": "jonesroadbeauty.com"
}
```

### 2.2 Get Score by Domain

**GET** `/api/v1/score/:domain`

Returns the most recent stored score for a domain. Returns `404` if no score exists.

### 2.3 List Scores

**GET** `/api/v1/scores`

Query params:
| Param       | Type    | Default | Description                     |
| ----------- | ------- | ------- | ------------------------------- |
| `tier`      | string  | —       | Filter by tier (e.g., `Tier 1`) |
| `min_score` | integer | —       | Minimum total score             |
| `max_score` | integer | —       | Maximum total score             |
| `page`      | integer | 1       | Page number                     |
| `limit`     | integer | 50      | Results per page (max 200)      |
| `sort`      | string  | `created_at` | Sort field               |
| `order`     | string  | `desc`  | `asc` or `desc`                 |

### 2.4 Update Overrides (Admin)

**PATCH** `/api/v1/score/:domain/overrides`

Request:
```json
{
  "gmv_override": 50000000,
  "industry_override": "Beauty",
  "known_brand": true,
  "recognized_exec": true,
  "locked": false
}
```

All fields optional. Setting a field to `null` clears the override.

### 2.5 Bulk Upload

**POST** `/api/v1/scores/bulk`

Request: `multipart/form-data` with CSV file.

CSV format:
```
domain
jonesroadbeauty.com
glossier.com
brooklinen.com
```

Response `202 Accepted`:
```json
{
  "job_id": "bulk-abc123",
  "total_domains": 3,
  "status": "processing"
}
```

### 2.6 Bulk Job Status

**GET** `/api/v1/scores/bulk/:job_id`

Response:
```json
{
  "job_id": "bulk-abc123",
  "status": "completed",
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "failures": [
    { "domain": "baddomain.xyz", "error": "STORELEADS_NOT_FOUND" }
  ]
}
```

### 2.7 Export

**GET** `/api/v1/scores/export?format=csv`

Returns CSV download of all scored domains with current filters applied.

---

## 3. StoreLeads API Integration

### 3.1 Endpoint

```
GET https://api.storeleads.app/v1/lookup?domain={domain}
Authorization: Bearer {STORELEADS_API_KEY}
```

### 3.2 Expected Response Fields

| Field                     | Type    | Used For           |
| ------------------------- | ------- | ------------------ |
| `domain`                  | string  | Identification     |
| `estimated_monthly_sales` | integer | GMV calculation    |
| `platform`                | string  | Metadata (stored)  |
| `category`                | string  | Industry scoring   |

### 3.3 Retry Strategy

| Attempt | Delay   |
| ------- | ------- |
| 1       | 0ms     |
| 2       | 1000ms  |
| 3       | 3000ms  |

- Max retries: 3
- Retry on: `5xx` status codes, network timeouts
- Do NOT retry on: `4xx` status codes (client errors, not found)
- Request timeout: 5 seconds per attempt

### 3.4 Rate Limiting

- Respect StoreLeads rate limits via response headers
- Implement client-side rate limiting: max 10 requests/second
- Bulk uploads processed via queue to stay within limits

### 3.5 Error Handling

| Scenario                        | Behavior                                          |
| ------------------------------- | ------------------------------------------------- |
| API returns `null` sales        | Store score with flag `REVENUE_UNKNOWN`, GMV = 0  |
| Domain not found (404)          | Return error `STORELEADS_NOT_FOUND`               |
| API timeout after retries       | Return error `STORELEADS_UNAVAILABLE`              |
| Invalid/malformed response      | Return error `STORELEADS_INVALID_RESPONSE`         |

---

## 4. Scoring Engine Logic

### 4.1 GMV Score Calculation

```typescript
function calculateGmvScore(annualGmv: number): number {
  if (annualGmv >= 100_000_000) return 5;
  if (annualGmv >= 25_000_000) return 4;
  if (annualGmv >= 10_000_000) return 3;
  if (annualGmv >= 5_000_000) return 2;
  return 1;
}
```

- `annualGmv = estimated_monthly_sales * 12`
- Revenue band boundaries are **inclusive on the lower bound**
- If `gmv_override` is set, use that value instead of API data

### 4.2 Industry Score Calculation

**3-Point Industries:**
`Beauty`, `Furniture`, `Health & Wellness`, `Supplements`

**1-Point Industries:**
`Apparel`, `Jewelry`, `Food & Beverage`, `CPG`

**Resolution order:**
1. `industry_override` (admin-set value) — highest priority
2. StoreLeads `category` field — mapped against known list
3. Keyword-based classification from domain/description — fallback
4. Default to `1` and flag `INDUSTRY_UNMATCHED` for manual review

Industry matching is **case-insensitive**. Partial matches supported (e.g., `"Health"` matches `"Health & Wellness"`).

### 4.3 Recognition Score Calculation

```typescript
function calculateRecognitionScore(knownBrand: boolean, recognizedExec: boolean): number {
  if (knownBrand && recognizedExec) return 2;
  if (knownBrand) return 1;
  return 0;
}
```

- Both flags default to `false` for new domains
- Only settable via admin UI or API override

### 4.4 Total Score & Tier

```typescript
const totalScore = gmvScore + industryScore + recognitionScore;
// Range: 1–10
```

| Score | Tier   |
| ----- | ------ |
| 9–10  | Tier 1 |
| 7–8   | Tier 2 |
| 5–6   | Tier 3 |
| 3–4   | Tier 4 |
| 1–2   | Tier 5 |

### 4.5 Locked Scores

When `locked = true`:
- Scoring endpoint skips recalculation
- Returns stored score as-is
- Override updates still allowed (require explicit unlock first via `locked: false`)

---

## 5. Database Schema

### 5.1 Table: `upscale_scores`

```sql
CREATE TABLE upscale_scores (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain                  VARCHAR(255) NOT NULL UNIQUE,
  estimated_monthly_sales BIGINT,
  estimated_annual_gmv    BIGINT,
  gmv_score               INTEGER NOT NULL DEFAULT 1,
  industry                VARCHAR(255),
  industry_score          INTEGER NOT NULL DEFAULT 1,
  known_brand             BOOLEAN NOT NULL DEFAULT FALSE,
  recognized_exec         BOOLEAN NOT NULL DEFAULT FALSE,
  recognition_score       INTEGER NOT NULL DEFAULT 0,
  total_score             INTEGER NOT NULL DEFAULT 1,
  tier                    VARCHAR(10) NOT NULL DEFAULT 'Tier 5',
  platform                VARCHAR(100),
  gmv_override            BIGINT,
  industry_override       VARCHAR(255),
  locked                  BOOLEAN NOT NULL DEFAULT FALSE,
  flags                   TEXT[] DEFAULT '{}',
  scored_at               TIMESTAMP WITH TIME ZONE,
  created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_upscale_scores_domain ON upscale_scores (domain);
CREATE INDEX idx_upscale_scores_tier ON upscale_scores (tier);
CREATE INDEX idx_upscale_scores_total_score ON upscale_scores (total_score);
```

### 5.2 Table: `bulk_jobs`

```sql
CREATE TABLE bulk_jobs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status      VARCHAR(20) NOT NULL DEFAULT 'processing',
  total       INTEGER NOT NULL DEFAULT 0,
  succeeded   INTEGER NOT NULL DEFAULT 0,
  failed      INTEGER NOT NULL DEFAULT 0,
  failures    JSONB DEFAULT '[]',
  created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 5.3 Table: `score_audit_log`

```sql
CREATE TABLE score_audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain      VARCHAR(255) NOT NULL,
  action      VARCHAR(50) NOT NULL,
  changes     JSONB NOT NULL,
  performed_by VARCHAR(255),
  created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

Tracks all overrides and manual changes for accountability.

---

## 6. Project Structure

```
upscale-points/
├── src/
│   ├── server.ts                 # Express app entrypoint
│   ├── config/
│   │   └── index.ts              # Env vars, constants
│   ├── routes/
│   │   └── scores.ts             # API route handlers
│   ├── services/
│   │   ├── scoring.service.ts    # Core scoring logic
│   │   ├── storeleads.service.ts # StoreLeads API client
│   │   └── bulk.service.ts       # Bulk upload processing
│   ├── models/
│   │   └── score.ts              # Type definitions
│   ├── middleware/
│   │   ├── errorHandler.ts       # Global error handling
│   │   └── validate.ts           # Request validation
│   └── utils/
│       ├── industry.ts           # Industry mapping tables
│       └── retry.ts              # Retry with backoff
├── prisma/
│   └── schema.prisma             # Database schema
├── admin/                        # React admin UI (Vite)
│   ├── src/
│   └── ...
├── tests/
│   ├── scoring.test.ts
│   ├── storeleads.test.ts
│   └── api.test.ts
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── tsconfig.json
├── package.json
└── README.md
```

---

## 7. Environment Variables

```
# Server
PORT=3000
NODE_ENV=production

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/upscale_points

# StoreLeads
STORELEADS_API_KEY=sk_live_...
STORELEADS_BASE_URL=https://api.storeleads.app/v1
STORELEADS_TIMEOUT_MS=5000
STORELEADS_MAX_RETRIES=3
STORELEADS_RATE_LIMIT_RPS=10
```

---

## 8. Performance Requirements

| Metric                          | Target        |
| ------------------------------- | ------------- |
| Single domain score latency     | < 3 seconds   |
| StoreLeads lookup success rate  | >= 95%        |
| API response (cached/stored)    | < 200ms       |
| Bulk upload throughput          | ~10 domains/s |
| Database query (list/filter)    | < 100ms       |

---

## 9. Testing Strategy

### 9.1 Unit Tests
- Scoring logic: GMV bands, industry mapping, recognition calculation
- Edge cases: null sales, unknown industry, boundary values
- Tier classification for all score ranges

### 9.2 Integration Tests
- StoreLeads API client with mocked responses
- Full score flow: input domain → stored result
- Override application and score recalculation
- Bulk upload processing

### 9.3 API Tests
- All endpoints: success, validation errors, not found
- CSV upload parsing and error handling
- Pagination and filtering

### 9.4 Key Test Cases

| Case                              | Input                        | Expected              |
| --------------------------------- | ---------------------------- | --------------------- |
| Max score brand                   | $100M+ GMV, Beauty, known+exec | Score 10, Tier 1   |
| Min score brand                   | $0-5M GMV, unknown industry  | Score 2, Tier 5       |
| Null revenue from API             | sales = null                 | Flag `REVENUE_UNKNOWN` |
| GMV boundary ($5M exactly)        | monthly = 416667             | GMV score = 2         |
| Locked score with rescore request | locked = true                | Return stored score   |
| Industry partial match            | category = "Health"          | Score = 3             |
| Override GMV                      | gmv_override = 50M           | Recalculate with 50M  |

---

## 10. Security

- API key stored in environment variables, never committed
- StoreLeads key encrypted at rest in production
- Admin endpoints protected by authentication (API key or session-based, TBD based on deployment)
- Input validation on all endpoints (domain format, numeric ranges)
- SQL injection prevented via Prisma parameterized queries
- Rate limiting on public-facing endpoints

---

## 11. Deployment

### Docker Compose (Development)

```yaml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    env_file: .env
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: upscale_points
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## 12. Implementation Phases

### Phase 1 — Core Engine (MVP)
- Project scaffolding (Express + TypeScript + Prisma)
- Database schema and migrations
- StoreLeads API client with retry logic
- Scoring service (GMV, industry, recognition)
- `POST /api/v1/score` and `GET /api/v1/score/:domain`
- Unit + integration tests

### Phase 2 — Admin & Bulk
- Override endpoints (`PATCH`)
- Bulk upload (CSV parse + queue)
- Export endpoint (CSV download)
- `GET /api/v1/scores` with filtering/pagination
- Audit log

### Phase 3 — Admin UI
- React admin dashboard
- Domain search and score display
- Override forms
- Bulk upload UI
- Export button

### Phase 4 — Hardening
- Authentication/authorization
- Rate limiting
- Monitoring and alerting
- Docker production config
- CI/CD pipeline
