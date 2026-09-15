/**
 * Research formatting utilities.
 *
 * Pure functions only.
 * No React or API dependencies.
 */

import type {
  ResearchClaim,
  ResearchExecution,
  ResearchEvidence,
  ResearchPlan,
  ResearchSource,
  ResearchStatus,
} from "../../research/types";

/**
 * Human-readable research status.
 */
export function formatResearchStatus(
  status: ResearchStatus,
): string {
  const labels: Record<ResearchStatus, string> = {
    idle: "Idle",
    planning: "Planning research",
    searching: "Searching",
    retrieving: "Retrieving evidence",
    synthesizing: "Synthesizing answer",
    verifying: "Verifying answer",
    completed: "Completed",
    failed: "Failed",
    cancelled: "Cancelled",
  };

  return labels[status] ?? status;
}

/**
 * Format a research status as a short UI label.
 */
export function formatResearchStatusShort(
  status: ResearchStatus,
): string {
  const labels: Record<ResearchStatus, string> = {
    idle: "Idle",
    planning: "Planning",
    searching: "Searching",
    retrieving: "Retrieving",
    synthesizing: "Synthesizing",
    verifying: "Verifying",
    completed: "Complete",
    failed: "Failed",
    cancelled: "Cancelled",
  };

  return labels[status] ?? status;
}

/**
 * Convert a score from 0-1 into a percentage.
 */
export function formatScore(
  score?: number,
  fallback = "—",
): string {
  if (score === undefined || Number.isNaN(score)) {
    return fallback;
  }

  const normalized = Math.min(
    1,
    Math.max(0, score),
  );

  return `${Math.round(normalized * 100)}%`;
}

/**
 * Format confidence.
 */
export function formatConfidence(
  confidence?: number,
): string {
  return formatScore(confidence);
}

/**
 * Format research progress.
 */
export function formatProgress(
  progress?: number,
): string {
  if (progress === undefined || Number.isNaN(progress)) {
    return "0%";
  }

  return `${Math.round(
    Math.min(100, Math.max(0, progress)),
  )}%`;
}

/**
 * Format source type.
 */
export function formatSourceType(
  source: ResearchSource,
): string {
  switch (source.source_type) {
    case "web":
      return "Web";

    case "paper":
      return "Research Paper";

    case "document":
      return "Document";

    case "database":
      return "Database";

    default:
      return "Source";
  }
}

/**
 * Return a safe domain name from a URL.
 */
export function getSourceDomain(
  source: ResearchSource,
): string {
  if (source.domain) {
    return source.domain;
  }

  if (!source.url) {
    return "Unknown source";
  }

  try {
    return new URL(source.url).hostname.replace(
      /^www\./,
      "",
    );
  } catch {
    return "Unknown source";
  }
}

/**
 * Create a compact source label.
 */
export function formatSourceLabel(
  source: ResearchSource,
): string {
  const domain = getSourceDomain(source);

  if (source.author) {
    return `${source.author} · ${domain}`;
  }

  return domain;
}

/**
 * Format a research plan for display.
 */
export function formatResearchPlan(
  plan?: ResearchPlan,
): string {
  if (!plan) {
    return "No research plan available.";
  }

  if (plan.steps.length === 0) {
    return plan.objective;
  }

  return [
    plan.objective,
    "",
    ...plan.steps.map(
      (step, index) =>
        `${index + 1}. ${step.title} — ${step.description}`,
    ),
  ].join("\n");
}

/**
 * Calculate how many claims are supported.
 */
export function getSupportedClaimCount(
  claims: ResearchClaim[],
): number {
  return claims.filter(
    (claim) => claim.supported,
  ).length;
}

/**
 * Calculate claim verification percentage.
 */
export function getClaimVerificationRate(
  claims: ResearchClaim[],
): number {
  if (claims.length === 0) {
    return 0;
  }

  return Math.round(
    (getSupportedClaimCount(claims) /
      claims.length) *
      100,
  );
}

/**
 * Format claim verification summary.
 */
export function formatClaimVerification(
  claims: ResearchClaim[],
): string {
  if (claims.length === 0) {
    return "No claims to verify.";
  }

  const supported = getSupportedClaimCount(claims);

  return `${supported} of ${claims.length} claims supported`;
}

/**
 * Find evidence belonging to a claim.
 */
export function getEvidenceForClaim(
  claim: ResearchClaim,
  evidence: ResearchEvidence[],
): ResearchEvidence[] {
  const ids = new Set(claim.evidence_ids);

  return evidence.filter((item) =>
    ids.has(item.id),
  );
}

/**
 * Format an execution title.
 */
export function formatResearchTitle(
  execution: ResearchExecution,
): string {
  if (execution.answer?.title) {
    return execution.answer.title;
  }

  if (execution.query.length <= 80) {
    return execution.query;
  }

  return `${execution.query.slice(0, 77)}...`;
}

/**
 * Format execution duration.
 */
export function formatResearchDuration(
  execution: ResearchExecution,
): string {
  if (!execution.started_at) {
    return "—";
  }

  const start = new Date(
    execution.started_at,
  ).getTime();

  const end = execution.completed_at
    ? new Date(
        execution.completed_at,
      ).getTime()
    : Date.now();

  if (
    Number.isNaN(start) ||
    Number.isNaN(end) ||
    end < start
  ) {
    return "—";
  }

  const seconds = Math.floor(
    (end - start) / 1000,
  );

  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return `${hours}h ${remainingMinutes}m`;
}

/**
 * Format ISO timestamp for the UI.
 */
export function formatResearchDate(
  value?: string,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}