import { z } from "zod";
import type { Request, Response, NextFunction } from "express";

export const scoreDomainSchema = z.object({
  domain: z
    .string()
    .min(1, "Domain is required")
    .regex(
      /^[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}$/,
      "Invalid domain format"
    ),
});

export const overrideSchema = z.object({
  gmv_override: z.number().nullable().optional(),
  industry_override: z.string().nullable().optional(),
  known_brand: z.boolean().optional(),
  recognized_exec: z.boolean().optional(),
  locked: z.boolean().optional(),
});

export const listScoresSchema = z.object({
  tier: z.string().optional(),
  min_score: z.coerce.number().int().min(1).max(10).optional(),
  max_score: z.coerce.number().int().min(1).max(10).optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(50),
  sort: z.enum(["created_at", "total_score", "domain", "tier"]).default("created_at"),
  order: z.enum(["asc", "desc"]).default("desc"),
});

export function validateBody(schema: z.ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      res.status(400).json({
        error: "VALIDATION_ERROR",
        details: result.error.issues,
      });
      return;
    }
    req.body = result.data;
    next();
  };
}

export function validateQuery(schema: z.ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      res.status(400).json({
        error: "VALIDATION_ERROR",
        details: result.error.issues,
      });
      return;
    }
    req.query = result.data;
    next();
  };
}
