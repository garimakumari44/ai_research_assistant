import type {
  AdaptiveRAGTrace,
  RAGTraceStep,
  TraceStepStatus,
} from "../types";

export interface FormattedTraceStep {
  id: string;
  index: number;
  title: string;
  description: string;
  status: TraceStepStatus;
  durationMs: number | null;
  durationLabel: string;
  strategy?: string;
  metadata: Record<string, unknown>;
}

export interface FormattedTrace {
  steps: FormattedTraceStep[];
  totalDurationMs: number | null;
  totalDurationLabel: string;
  completedSteps: number;
  failedSteps: number;
  retrievalSteps: number;
  generationSteps: number;
}

function formatDuration(durationMs: number | null | undefined): string {
  if (durationMs == null || Number.isNaN(durationMs)) {
    return "—";
  }

  if (durationMs < 1000) {
    return `${Math.round(durationMs)} ms`;
  }

  if (durationMs < 60_000) {
    return `${(durationMs / 1000).toFixed(2)} s`;
  }

  const minutes = Math.floor(durationMs / 60_000);
  const seconds = Math.round((durationMs % 60_000) / 1000);

  return `${minutes}m ${seconds}s`;
}

function humanize(value: string | undefined | null): string {
  if (!value) {
    return "";
  }

  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getStepTitle(step: RAGTraceStep): string {
  if (step.title) {
    return step.title;
  }

  if (step.name) {
    return humanize(step.name);
  }

  if (step.type) {
    return humanize(step.type);
  }

  return `Step ${step.index + 1}`;
}

function getStepDescription(step: RAGTraceStep): string {
  if (step.description) {
    return step.description;
  }

  switch (step.type) {
    case "planning":
      return "Adaptive controller created an execution plan.";

    case "routing":
      return "The router selected the next RAG strategy.";

    case "retrieval":
      return "Relevant knowledge was retrieved from the knowledge base.";

    case "evaluation":
      return "Retrieved evidence was evaluated for relevance and quality.";

    case "generation":
      return "The language model generated a response from the selected evidence.";

    case "refinement":
      return "The query or retrieval plan was refined.";

    case "stopping":
      return "The controller evaluated whether execution should stop.";

    default:
      return "Adaptive RAG execution step.";
  }
}

function getStepStatus(
  step: RAGTraceStep,
): TraceStepStatus {
  if (step.status) {
    return step.status;
  }

  if (step.error) {
    return "failed";
  }

  return "completed";
}

function getStepDuration(
  step: RAGTraceStep,
): number | null {
  if (typeof step.duration_ms === "number") {
    return step.duration_ms;
  }

  if (
    typeof step.started_at === "number" &&
    typeof step.finished_at === "number"
  ) {
    return Math.max(0, step.finished_at - step.started_at);
  }

  return null;
}

export function formatTrace(
  trace: AdaptiveRAGTrace | null | undefined,
): FormattedTrace {
  if (!trace) {
    return {
      steps: [],
      totalDurationMs: null,
      totalDurationLabel: "—",
      completedSteps: 0,
      failedSteps: 0,
      retrievalSteps: 0,
      generationSteps: 0,
    };
  }

  const rawSteps = trace.steps ?? [];

  const steps = rawSteps.map((step, index) => {
    const durationMs = getStepDuration(step);

    return {
      id: step.id ?? `trace-step-${index}`,
      index,
      title: getStepTitle({
        ...step,
        index,
      }),
      description: getStepDescription(step),
      status: getStepStatus(step),
      durationMs,
      durationLabel: formatDuration(durationMs),
      strategy: step.strategy,
      metadata: step.metadata ?? {},
    };
  });

  const totalDurationMs =
    typeof trace.total_duration_ms === "number"
      ? trace.total_duration_ms
      : steps.reduce(
          (total, step) => total + (step.durationMs ?? 0),
          0,
        );

  return {
    steps,
    totalDurationMs,
    totalDurationLabel: formatDuration(totalDurationMs),
    completedSteps: steps.filter(
      (step) => step.status === "completed",
    ).length,
    failedSteps: steps.filter(
      (step) => step.status === "failed",
    ).length,
    retrievalSteps: steps.filter(
      (step) => step.metadata.category === "retrieval" ||
        step.title.toLowerCase().includes("retriev"),
    ).length,
    generationSteps: steps.filter(
      (step) => step.metadata.category === "generation" ||
        step.title.toLowerCase().includes("generat"),
    ).length,
  };
}

export function formatTraceStep(
  step: RAGTraceStep,
  index = 0,
): FormattedTraceStep {
  const durationMs = getStepDuration(step);

  return {
    id: step.id ?? `trace-step-${index}`,
    index,
    title: getStepTitle({
      ...step,
      index,
    }),
    description: getStepDescription(step),
    status: getStepStatus(step),
    durationMs,
    durationLabel: formatDuration(durationMs),
    strategy: step.strategy,
    metadata: step.metadata ?? {},
  };
}

export function formatTraceDuration(
  durationMs: number | null | undefined,
): string {
  return formatDuration(durationMs);
}

export function getTraceStatusLabel(
  status: TraceStepStatus,
): string {
  switch (status) {
    case "running":
      return "Running";

    case "completed":
      return "Completed";

    case "failed":
      return "Failed";

    case "skipped":
      return "Skipped";

    case "pending":
      return "Pending";

    default:
      return humanize(status);
  }
}