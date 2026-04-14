import type { Request, Response, NextFunction } from "express";
import { StoreLeadsError } from "../services/storeleads.service";

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  console.error(`[ERROR] ${err.message}`);

  if (err instanceof StoreLeadsError) {
    const status = err.statusCode === 404 ? 404 : 502;
    res.status(status).json({
      error: err.code,
      message: err.message,
    });
    return;
  }

  if (err.message.startsWith("Score not found")) {
    res.status(404).json({
      error: "NOT_FOUND",
      message: err.message,
    });
    return;
  }

  res.status(500).json({
    error: "INTERNAL_ERROR",
    message:
      process.env.NODE_ENV === "production"
        ? "Internal server error"
        : err.message,
  });
}
