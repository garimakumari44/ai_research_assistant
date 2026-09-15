"use client";

import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  Copy,
  Database,
  FileText,
  GitBranch,
  Loader2,
  MessageSquare,
  Search,
  Sparkles,
  Terminal,
} from "lucide-react";

import { useMemo, useState } from "react";

export type TraceStage =
  | "query"
  | "plan"
  | "retrieval"
  | "documents"
  | "evidence"
  | "generation"
  | "answer";

export type TraceStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export interface TraceEvent {
  id: string;
  stage: TraceStage;
  status: TraceStatus;
  timestamp?: string;
  durationMs?: number;
  input?: unknown;
  output?: unknown;
  metadata?: Record<string, unknown>;
  error?: string;
}

interface TraceViewerProps {
  traceId?: string;
  query?: string;
  events?: TraceEvent[];
  loading?: boolean;
}

const stageConfig: Record<
  TraceStage,
  {
    label: string;
    icon: typeof Search;
  }
> = {
  query: {
    label: "Query",
    icon: MessageSquare,
  },
  plan: {
    label: "Plan",
    icon: GitBranch,
  },
  retrieval: {
    label: "Retrieval",
    icon: Search,
  },
  documents: {
    label: "Documents",
    icon: Database,
  },
  evidence: {
    label: "Evidence",
    icon: FileText,
  },
  generation: {
    label: "Generation",
    icon: Sparkles,
  },
  answer: {
    label: "Answer",
    icon: CheckCircle2,
  },
};

const statusStyles: Record<TraceStatus, string> = {
  pending: "text-zinc-600 border-zinc-800 bg-zinc-900",
  running: "text-blue-400 border-blue-500/20 bg-blue-500/10",
  completed:
    "text-emerald-400 border-emerald-500/20 bg-emerald-500/10",
  failed: "text-red-400 border-red-500/20 bg-red-500/10",
  skipped: "text-amber-400 border-amber-500/20 bg-amber-500/10",
};

function formatDuration(duration?: number) {
  if (duration === undefined) return "—";

  if (duration < 1000) {
    return `${duration} ms`;
  }

  return `${(duration / 1000).toFixed(2)} s`;
}

function formatTime(timestamp?: string) {
  if (!timestamp) return "";

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function serialize(value: unknown) {
  if (value === undefined || value === null) {
    return "No data";
  }

  if (typeof value === "string") {
    return value;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function TraceViewer({
  traceId,
  query,
  events = [],
  loading = false,
}: TraceViewerProps) {
  const [expanded, setExpanded] = useState<string | null>(
    events[0]?.id ?? null,
  );

  const totalDuration = useMemo(
    () =>
      events.reduce(
        (total, event) => total + (event.durationMs ?? 0),
        0,
      ),
    [events],
  );

  const completed = events.filter(
    (event) => event.status === "completed",
  ).length;

  const failed = events.filter(
    (event) => event.status === "failed",
  ).length;

  const toggle = (id: string) => {
    setExpanded((current) => (current === id ? null : id));
  };

  const copyValue = async (value: unknown) => {
    try {
      await navigator.clipboard.writeText(serialize(value));
    } catch {
      // Clipboard access may be unavailable.
    }
  };

  return (
    <section className="flex h-full flex-col bg-zinc-950">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <Terminal className="h-5 w-5 text-zinc-400" />

          <div className="min-w-0 flex-1">
            <h1 className="text-sm font-semibold text-zinc-200">
              Execution Trace
            </h1>

            {traceId && (
              <p className="mt-0.5 truncate font-mono text-[11px] text-zinc-600">
                {traceId}
              </p>
            )}
          </div>

          {loading && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
          )}
        </div>

        {query && (
          <div className="mt-4 rounded-md border border-zinc-800 bg-zinc-900/40 px-3 py-2">
            <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              Query
            </span>

            <p className="mt-1 text-sm text-zinc-300">{query}</p>
          </div>
        )}

        <div className="mt-4 flex items-center gap-5 text-xs text-zinc-600">
          <span>
            {completed}/{events.length} stages completed
          </span>

          {failed > 0 && (
            <span className="text-red-400">
              {failed} failed
            </span>
          )}

          <span className="inline-flex items-center gap-1">
            <Clock3 className="h-3.5 w-3.5" />
            {formatDuration(totalDuration)}
          </span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {events.length === 0 ? (
          <div className="flex min-h-[300px] items-center justify-center">
            <div className="text-center">
              <Terminal className="mx-auto h-7 w-7 text-zinc-700" />

              <p className="mt-3 text-sm text-zinc-500">
                No trace events available.
              </p>
            </div>
          </div>
        ) : (
          <div className="relative mx-auto max-w-4xl">
            <div className="absolute bottom-6 left-[19px] top-6 w-px bg-zinc-800" />

            <div className="space-y-3">
              {events.map((event) => {
                const config = stageConfig[event.stage];
                const Icon = config.icon;
                const isExpanded = expanded === event.id;

                return (
                  <div
                    key={event.id}
                    className="relative flex gap-4"
                  >
                    <div
                      className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border ${statusStyles[event.status]}`}
                    >
                      {event.status === "running" ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : event.status === "failed" ? (
                        <AlertCircle className="h-4 w-4" />
                      ) : (
                        <Icon className="h-4 w-4" />
                      )}
                    </div>

                    <div className="min-w-0 flex-1 rounded-lg border border-zinc-800 bg-zinc-950">
                      <button
                        type="button"
                        onClick={() => toggle(event.id)}
                        className="flex w-full items-center gap-3 px-4 py-3 text-left"
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-zinc-600" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-zinc-600" />
                        )}

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-zinc-300">
                              {config.label}
                            </span>

                            <span
                              className={`rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide ${statusStyles[event.status]}`}
                            >
                              {event.status}
                            </span>
                          </div>

                          <div className="mt-1 flex items-center gap-3 text-[11px] text-zinc-600">
                            {event.timestamp && (
                              <span>
                                {formatTime(event.timestamp)}
                              </span>
                            )}

                            <span>
                              {formatDuration(event.durationMs)}
                            </span>
                          </div>
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="border-t border-zinc-800 p-4">
                          {event.error && (
                            <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/5 p-3 text-xs text-red-400">
                              {event.error}
                            </div>
                          )}

                          <TraceDataBlock
                            label="Input"
                            value={event.input}
                            onCopy={() => copyValue(event.input)}
                          />

                          <TraceDataBlock
                            label="Output"
                            value={event.output}
                            onCopy={() => copyValue(event.output)}
                          />

                          {event.metadata && (
                            <TraceDataBlock
                              label="Metadata"
                              value={event.metadata}
                              onCopy={() =>
                                copyValue(event.metadata)
                              }
                            />
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function TraceDataBlock({
  label,
  value,
  onCopy,
}: {
  label: string;
  value: unknown;
  onCopy: () => void;
}) {
  if (value === undefined || value === null) {
    return null;
  }

  return (
    <div className="mb-4 last:mb-0">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
          {label}
        </span>

        <button
          type="button"
          onClick={onCopy}
          className="rounded p-1 text-zinc-700 transition hover:bg-zinc-800 hover:text-zinc-400"
          aria-label={`Copy ${label}`}
        >
          <Copy className="h-3.5 w-3.5" />
        </button>
      </div>

      <pre className="max-h-64 overflow-auto rounded-md border border-zinc-800 bg-black/40 p-3 font-mono text-[11px] leading-5 text-zinc-500">
        {serialize(value)}
      </pre>
    </div>
  );
}