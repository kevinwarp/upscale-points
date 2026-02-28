export interface StoreLeadsResponse {
  domain: string;
  estimated_monthly_sales: number | null;
  platform: string | null;
  category: string | null;
}

export interface ScoreResult {
  id: string;
  domain: string;
  estimated_monthly_sales: number | null;
  estimated_annual_gmv: number | null;
  gmv_score: number;
  industry: string | null;
  industry_score: number;
  known_brand: boolean;
  recognized_exec: boolean;
  recognition_score: number;
  total_upscale_score: number;
  tier: string;
  platform: string | null;
  flags: string[];
  created_at: Date;
}

export interface OverrideInput {
  gmv_override?: number | null;
  industry_override?: string | null;
  known_brand?: boolean;
  recognized_exec?: boolean;
  locked?: boolean;
}

export interface BulkJobResult {
  job_id: string;
  status: string;
  total: number;
  succeeded: number;
  failed: number;
  failures: Array<{ domain: string; error: string }>;
}
