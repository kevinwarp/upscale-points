import { config } from "../config";
import { withRetry } from "../utils/retry";
import type { StoreLeadsResponse } from "../models/score";

export class StoreLeadsError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = "StoreLeadsError";
  }
}

function isRetryable(error: unknown): boolean {
  if (error instanceof StoreLeadsError) {
    return (
      error.statusCode !== undefined &&
      error.statusCode >= 500 &&
      error.statusCode < 600
    );
  }
  return true; // Retry on network errors
}

export async function lookupDomain(
  domain: string
): Promise<StoreLeadsResponse> {
  const { apiKey, baseUrl, timeoutMs, maxRetries } = config.storeleads;

  return withRetry(
    async () => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);

      try {
        const res = await fetch(
          `${baseUrl}/lookup?domain=${encodeURIComponent(domain)}`,
          {
            headers: { Authorization: `Bearer ${apiKey}` },
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          if (res.status === 404) {
            throw new StoreLeadsError(
              "STORELEADS_NOT_FOUND",
              `Domain not found: ${domain}`,
              404
            );
          }
          throw new StoreLeadsError(
            "STORELEADS_ERROR",
            `StoreLeads API error: ${res.status}`,
            res.status
          );
        }

        const data = (await res.json()) as Record<string, unknown>;

        if (!data || typeof data !== "object" || !("domain" in data)) {
          throw new StoreLeadsError(
            "STORELEADS_INVALID_RESPONSE",
            "Invalid response from StoreLeads"
          );
        }

        return data as unknown as StoreLeadsResponse;
      } catch (error) {
        if (error instanceof StoreLeadsError) throw error;

        if (
          error instanceof Error &&
          error.name === "AbortError"
        ) {
          throw new StoreLeadsError(
            "STORELEADS_UNAVAILABLE",
            `StoreLeads API timeout after ${timeoutMs}ms`
          );
        }

        throw new StoreLeadsError(
          "STORELEADS_UNAVAILABLE",
          `StoreLeads API unreachable: ${error instanceof Error ? error.message : "unknown error"}`
        );
      } finally {
        clearTimeout(timeout);
      }
    },
    maxRetries,
    isRetryable
  );
}
