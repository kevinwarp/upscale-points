const BACKOFF_DELAYS = [0, 1000, 3000];

export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number,
  shouldRetry: (error: unknown) => boolean = () => true
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (!shouldRetry(error) || attempt === maxRetries - 1) {
        throw error;
      }
      const delay = BACKOFF_DELAYS[attempt] ?? 3000;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}
