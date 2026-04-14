export const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  nodeEnv: process.env.NODE_ENV || "development",

  storeleads: {
    apiKey: process.env.STORELEADS_API_KEY || "",
    baseUrl:
      process.env.STORELEADS_BASE_URL || "https://api.storeleads.app/v1",
    timeoutMs: parseInt(process.env.STORELEADS_TIMEOUT_MS || "5000", 10),
    maxRetries: parseInt(process.env.STORELEADS_MAX_RETRIES || "3", 10),
    rateLimitRps: parseInt(process.env.STORELEADS_RATE_LIMIT_RPS || "10", 10),
  },
} as const;
