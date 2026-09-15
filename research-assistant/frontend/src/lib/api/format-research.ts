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

export function formatResearchStatus(
  status: ResearchStatus,
): string {
  const labels: Partial<Record<ResearchStatus, string>> = {
    idle: "Idle",
    pending: "Pending",
    queued: "Queued",
    planning: "Planning research",
    searching: "Searching",
    retrieving: "Retrieving evidence",
    running: "Running research",
    synthesizing: "Synthesizing answer",
    verifying: "Verifying answer",
    completed: "Completed",
    failed: "Failed",
    cancelled: "Cancelled",
  };

  return labels[status] ?? status;
}

export function formatResearchStatusShort(
  status: ResearchStatus,
): string {
  const labels: Partial<Record<ResearchStatus, string>> = {
    idle: "Idle",
    pending: "Pending",
    queued: "Queued",
    planning: "Planning",
    searching: "Searching",
    retrieving: "Retrieving",
    running: "Running",
    synthesizing: "Synthesizing",
    verifying: "Verifying",
    completed: "Complete",
    failed: "Failed",
    cancelled: "Cancelled",
  };

  return labels[status] ?? status;
}

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

export function formatConfidence(
  confidence?: number,
): string {
  return formatScore(confidence);
}

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

    case "github":
      return "GitHub";

    case "documentation":
      return "Documentation";

    default:
      return "Source";
  }
}

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

export function formatSourceLabel(
  source: ResearchSource,
): string {
  const domain = getSourceDomain(source);

  const author =
    source.author ??
    source.authors?.[0];

  if (author) {
    return `${author} · ${domain}`;
  }

  return domain;
}

export function formatResearchPlan(
  plan?: ResearchPlan,
): string {
  if (!plan) {
    return "No research plan available.";
  }

  const objective =
    plan.objective ??
    "Research plan";

  const steps = plan.steps ?? [];

  if (steps.length === 0) {
    return objective;
  }

  return [
    objective,
    "",
    ...steps.map(
      (step, index) =>
        `${index + 1}. ${step.title ?? step.action ?? "Research step"} — ${step.description ?? ""}`,
    ),
  ].join("\n");
}

export function getSupportedClaimCount(
  claims: ResearchClaim[],
): number {
  return claims.filter(
    (claim) => claim.supported,
  ).length;
}

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

export function formatClaimVerification(
  claims: ResearchClaim[],
): string {
  if (claims.length === 0) {
    return "No claims to verify.";
  }

  const supported = getSupportedClaimCount(claims);

  return `${supported} of ${claims.length} claims supported`;
}

export function getEvidenceForClaim(
  claim: ResearchClaim,
  evidence: ResearchEvidence[],
): ResearchEvidence[] {
  const ids = new Set(
    claim.evidence_ids ?? [],
  );

  return evidence.filter((item) =>
    ids.has(item.id),
  );
}

export function formatResearchTitle(
  execution: ResearchExecution,
): string {
  if (execution.answer?.title) {
    return execution.answer.title;
  }

  const query =
    execution.query ??
    "Research";

  if (query.length <= 80) {
    return query;
  }

  return `${query.slice(0, 77)}...`;
}

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
