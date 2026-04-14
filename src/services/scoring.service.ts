import { PrismaClient } from "@prisma/client";
import { lookupDomain, StoreLeadsError } from "./storeleads.service";
import { getIndustryScore } from "../utils/industry";
import type { ScoreResult, OverrideInput } from "../models/score";

const prisma = new PrismaClient();

export function calculateGmvScore(annualGmv: number): number {
  if (annualGmv >= 100_000_000) return 5;
  if (annualGmv >= 25_000_000) return 4;
  if (annualGmv >= 10_000_000) return 3;
  if (annualGmv >= 5_000_000) return 2;
  return 1;
}

export function calculateRecognitionScore(
  knownBrand: boolean,
  recognizedExec: boolean
): number {
  if (knownBrand && recognizedExec) return 2;
  if (knownBrand) return 1;
  return 0;
}

export function calculateTier(totalScore: number): string {
  if (totalScore >= 9) return "Tier 1";
  if (totalScore >= 7) return "Tier 2";
  if (totalScore >= 5) return "Tier 3";
  if (totalScore >= 3) return "Tier 4";
  return "Tier 5";
}

function toScoreResult(record: {
  id: string;
  domain: string;
  estimatedMonthlySales: bigint | null;
  estimatedAnnualGmv: bigint | null;
  gmvScore: number;
  industry: string | null;
  industryScore: number;
  knownBrand: boolean;
  recognizedExec: boolean;
  recognitionScore: number;
  totalScore: number;
  tier: string;
  platform: string | null;
  flags: string[];
  createdAt: Date;
}): ScoreResult {
  return {
    id: record.id,
    domain: record.domain,
    estimated_monthly_sales: record.estimatedMonthlySales
      ? Number(record.estimatedMonthlySales)
      : null,
    estimated_annual_gmv: record.estimatedAnnualGmv
      ? Number(record.estimatedAnnualGmv)
      : null,
    gmv_score: record.gmvScore,
    industry: record.industry,
    industry_score: record.industryScore,
    known_brand: record.knownBrand,
    recognized_exec: record.recognizedExec,
    recognition_score: record.recognitionScore,
    total_upscale_score: record.totalScore,
    tier: record.tier,
    platform: record.platform,
    flags: record.flags,
    created_at: record.createdAt,
  };
}

export async function scoreDomain(domain: string): Promise<ScoreResult> {
  const normalized = domain.toLowerCase().trim();

  // Check if locked score exists
  const existing = await prisma.upscaleScore.findUnique({
    where: { domain: normalized },
  });

  if (existing?.locked) {
    return toScoreResult(existing);
  }

  // Fetch from StoreLeads
  const storeLeadsData = await lookupDomain(normalized);

  const flags: string[] = [];
  const monthlySales = storeLeadsData.estimated_monthly_sales;
  const annualGmv = monthlySales ? monthlySales * 12 : 0;

  if (monthlySales === null) {
    flags.push("REVENUE_UNKNOWN");
  }

  // GMV — use override if present
  const effectiveGmv =
    existing?.gmvOverride !== null && existing?.gmvOverride !== undefined
      ? Number(existing.gmvOverride)
      : annualGmv;
  const gmvScore = calculateGmvScore(effectiveGmv);

  // Industry — use override, then API, then default
  const effectiveIndustry =
    existing?.industryOverride ?? storeLeadsData.category;
  const { score: industryScore, matched: industryMatched } =
    getIndustryScore(effectiveIndustry);
  if (!industryMatched && !existing?.industryOverride) {
    flags.push("INDUSTRY_UNMATCHED");
  }

  // Recognition — preserve existing values
  const knownBrand = existing?.knownBrand ?? false;
  const recognizedExec = existing?.recognizedExec ?? false;
  const recognitionScore = calculateRecognitionScore(
    knownBrand,
    recognizedExec
  );

  const totalScore = gmvScore + industryScore + recognitionScore;
  const tier = calculateTier(totalScore);

  const record = await prisma.upscaleScore.upsert({
    where: { domain: normalized },
    update: {
      estimatedMonthlySales: monthlySales ? BigInt(monthlySales) : null,
      estimatedAnnualGmv: monthlySales ? BigInt(annualGmv) : null,
      gmvScore,
      industry: effectiveIndustry,
      industryScore,
      recognitionScore,
      totalScore,
      tier,
      platform: storeLeadsData.platform,
      flags,
      scoredAt: new Date(),
    },
    create: {
      domain: normalized,
      estimatedMonthlySales: monthlySales ? BigInt(monthlySales) : null,
      estimatedAnnualGmv: monthlySales ? BigInt(annualGmv) : null,
      gmvScore,
      industry: effectiveIndustry,
      industryScore,
      knownBrand,
      recognizedExec,
      recognitionScore,
      totalScore,
      tier,
      platform: storeLeadsData.platform,
      flags,
      scoredAt: new Date(),
    },
  });

  return toScoreResult(record);
}

export async function getScoreByDomain(
  domain: string
): Promise<ScoreResult | null> {
  const record = await prisma.upscaleScore.findUnique({
    where: { domain: domain.toLowerCase().trim() },
  });
  return record ? toScoreResult(record) : null;
}

export async function listScores(params: {
  tier?: string;
  minScore?: number;
  maxScore?: number;
  page: number;
  limit: number;
  sort: string;
  order: "asc" | "desc";
}): Promise<{ data: ScoreResult[]; total: number }> {
  const where: Record<string, unknown> = {};
  if (params.tier) where.tier = params.tier;
  if (params.minScore !== undefined || params.maxScore !== undefined) {
    where.totalScore = {
      ...(params.minScore !== undefined ? { gte: params.minScore } : {}),
      ...(params.maxScore !== undefined ? { lte: params.maxScore } : {}),
    };
  }

  const [records, total] = await Promise.all([
    prisma.upscaleScore.findMany({
      where,
      orderBy: { [params.sort]: params.order },
      skip: (params.page - 1) * params.limit,
      take: params.limit,
    }),
    prisma.upscaleScore.count({ where }),
  ]);

  return {
    data: records.map(toScoreResult),
    total,
  };
}

export async function applyOverrides(
  domain: string,
  overrides: OverrideInput
): Promise<ScoreResult> {
  const normalized = domain.toLowerCase().trim();

  const existing = await prisma.upscaleScore.findUnique({
    where: { domain: normalized },
  });
  if (!existing) {
    throw new Error(`Score not found for domain: ${normalized}`);
  }

  // Build update data
  const update: Record<string, unknown> = {};
  const changes: Record<string, unknown> = {};

  if (overrides.gmv_override !== undefined) {
    update.gmvOverride =
      overrides.gmv_override !== null
        ? BigInt(overrides.gmv_override)
        : null;
    changes.gmv_override = {
      from: existing.gmvOverride ? Number(existing.gmvOverride) : null,
      to: overrides.gmv_override,
    };
  }
  if (overrides.industry_override !== undefined) {
    update.industryOverride = overrides.industry_override;
    changes.industry_override = {
      from: existing.industryOverride,
      to: overrides.industry_override,
    };
  }
  if (overrides.known_brand !== undefined) {
    update.knownBrand = overrides.known_brand;
    changes.known_brand = {
      from: existing.knownBrand,
      to: overrides.known_brand,
    };
  }
  if (overrides.recognized_exec !== undefined) {
    update.recognizedExec = overrides.recognized_exec;
    changes.recognized_exec = {
      from: existing.recognizedExec,
      to: overrides.recognized_exec,
    };
  }
  if (overrides.locked !== undefined) {
    update.locked = overrides.locked;
    changes.locked = { from: existing.locked, to: overrides.locked };
  }

  // Recalculate scores with new overrides
  const effectiveGmv =
    (overrides.gmv_override !== undefined
      ? overrides.gmv_override
      : existing.gmvOverride
        ? Number(existing.gmvOverride)
        : null) ?? (existing.estimatedAnnualGmv ? Number(existing.estimatedAnnualGmv) : 0);

  const effectiveIndustry =
    (overrides.industry_override !== undefined
      ? overrides.industry_override
      : existing.industryOverride) ?? existing.industry;

  const knownBrand = overrides.known_brand ?? existing.knownBrand;
  const recognizedExec = overrides.recognized_exec ?? existing.recognizedExec;

  const gmvScore = calculateGmvScore(effectiveGmv);
  const { score: industryScore } = getIndustryScore(effectiveIndustry);
  const recognitionScore = calculateRecognitionScore(
    knownBrand,
    recognizedExec
  );
  const totalScore = gmvScore + industryScore + recognitionScore;
  const tier = calculateTier(totalScore);

  update.gmvScore = gmvScore;
  update.industryScore = industryScore;
  update.recognitionScore = recognitionScore;
  update.totalScore = totalScore;
  update.tier = tier;

  const record = await prisma.upscaleScore.update({
    where: { domain: normalized },
    data: update,
  });

  // Audit log
  await prisma.scoreAuditLog.create({
    data: {
      domain: normalized,
      action: "OVERRIDE",
      changes: JSON.parse(JSON.stringify(changes)),
    },
  });

  return toScoreResult(record);
}
