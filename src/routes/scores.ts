import { Router } from "express";
import multer from "multer";
import { PrismaClient } from "@prisma/client";
import {
  scoreDomain,
  getScoreByDomain,
  listScores,
  applyOverrides,
} from "../services/scoring.service";
import { processBulkUpload, getBulkJobStatus } from "../services/bulk.service";
import {
  validateBody,
  validateQuery,
  scoreDomainSchema,
  overrideSchema,
  listScoresSchema,
} from "../middleware/validate";

const router = Router();
const upload = multer({ storage: multer.memoryStorage() });
const prisma = new PrismaClient();

// POST /api/v1/score — Score a domain
router.post("/score", validateBody(scoreDomainSchema), async (req, res, next) => {
  try {
    const result = await scoreDomain(req.body.domain);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

// GET /api/v1/score/:domain — Get stored score
router.get("/score/:domain", async (req, res, next) => {
  try {
    const result = await getScoreByDomain(req.params.domain);
    if (!result) {
      res.status(404).json({
        error: "NOT_FOUND",
        message: `No score found for domain: ${req.params.domain}`,
      });
      return;
    }
    res.json(result);
  } catch (error) {
    next(error);
  }
});

// GET /api/v1/scores — List scores with filters
router.get("/scores", validateQuery(listScoresSchema), async (req, res, next) => {
  try {
    const query = req.query as unknown as {
      tier?: string;
      min_score?: number;
      max_score?: number;
      page: number;
      limit: number;
      sort: string;
      order: "asc" | "desc";
    };

    const result = await listScores({
      tier: query.tier,
      minScore: query.min_score,
      maxScore: query.max_score,
      page: query.page,
      limit: query.limit,
      sort: query.sort,
      order: query.order,
    });

    res.json({
      data: result.data,
      total: result.total,
      page: query.page,
      limit: query.limit,
    });
  } catch (error) {
    next(error);
  }
});

// PATCH /api/v1/score/:domain/overrides — Update overrides
router.patch(
  "/score/:domain/overrides",
  validateBody(overrideSchema),
  async (req, res, next) => {
    try {
      const result = await applyOverrides(req.params.domain as string, req.body);
      res.json(result);
    } catch (error) {
      next(error);
    }
  }
);

// POST /api/v1/scores/bulk — Bulk upload CSV
router.post("/scores/bulk", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) {
      res.status(400).json({
        error: "VALIDATION_ERROR",
        message: "CSV file is required",
      });
      return;
    }

    const { jobId, total } = await processBulkUpload(req.file.buffer);
    res.status(202).json({
      job_id: jobId,
      total_domains: total,
      status: "processing",
    });
  } catch (error) {
    next(error);
  }
});

// GET /api/v1/scores/bulk/:jobId — Bulk job status
router.get("/scores/bulk/:jobId", async (req, res, next) => {
  try {
    const status = await getBulkJobStatus(req.params.jobId);
    if (!status) {
      res.status(404).json({
        error: "NOT_FOUND",
        message: `Bulk job not found: ${req.params.jobId}`,
      });
      return;
    }
    res.json(status);
  } catch (error) {
    next(error);
  }
});

// GET /api/v1/scores/export — Export CSV
router.get("/scores/export", async (req, res, next) => {
  try {
    const records = await prisma.upscaleScore.findMany({
      orderBy: { totalScore: "desc" },
    });

    const csvHeader =
      "domain,estimated_monthly_sales,estimated_annual_gmv,gmv_score,industry,industry_score,recognition_score,total_score,tier,platform,flags\n";

    const csvRows = records
      .map(
        (r) =>
          `${r.domain},${r.estimatedMonthlySales ?? ""},${r.estimatedAnnualGmv ?? ""},${r.gmvScore},${r.industry ?? ""},${r.industryScore},${r.recognitionScore},${r.totalScore},${r.tier},${r.platform ?? ""},${r.flags.join(";")}`
      )
      .join("\n");

    res.setHeader("Content-Type", "text/csv");
    res.setHeader(
      "Content-Disposition",
      "attachment; filename=upscale_scores.csv"
    );
    res.send(csvHeader + csvRows);
  } catch (error) {
    next(error);
  }
});

export default router;
