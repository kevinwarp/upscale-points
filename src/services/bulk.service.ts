import { PrismaClient } from "@prisma/client";
import { parse } from "csv-parse/sync";
import { scoreDomain } from "./scoring.service";

const prisma = new PrismaClient();

export async function processBulkUpload(
  csvBuffer: Buffer
): Promise<{ jobId: string; total: number }> {
  const records = parse(csvBuffer, {
    columns: true,
    skip_empty_lines: true,
    trim: true,
  }) as Array<{ domain: string }>;

  const domains = records
    .map((r) => r.domain?.toLowerCase().trim())
    .filter(Boolean);

  const job = await prisma.bulkJob.create({
    data: {
      total: domains.length,
      status: "processing",
    },
  });

  // Process in background (non-blocking)
  processDomainsInBackground(job.id, domains).catch(console.error);

  return { jobId: job.id, total: domains.length };
}

async function processDomainsInBackground(
  jobId: string,
  domains: string[]
): Promise<void> {
  let succeeded = 0;
  let failed = 0;
  const failures: Array<{ domain: string; error: string }> = [];

  for (const domain of domains) {
    try {
      await scoreDomain(domain);
      succeeded++;
    } catch (error) {
      failed++;
      failures.push({
        domain,
        error:
          error instanceof Error ? error.message : "Unknown error",
      });
    }

    // Update progress
    await prisma.bulkJob.update({
      where: { id: jobId },
      data: { succeeded, failed, failures },
    });
  }

  await prisma.bulkJob.update({
    where: { id: jobId },
    data: { status: "completed", succeeded, failed, failures },
  });
}

export async function getBulkJobStatus(jobId: string) {
  const job = await prisma.bulkJob.findUnique({ where: { id: jobId } });
  if (!job) return null;

  return {
    job_id: job.id,
    status: job.status,
    total: job.total,
    succeeded: job.succeeded,
    failed: job.failed,
    failures: job.failures,
  };
}
