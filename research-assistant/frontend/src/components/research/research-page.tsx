"use client";

import {
  AlertCircle,
  Brain,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";

import { useResearch } from "@/research/hooks/use-research";
import type { ResearchReport } from "@/research/types";

import { ResearchInput } from "./research-input";

export interface ResearchPageProps {
  projectId?: string;
  collectionId?: string;
}

export function ResearchPage({
  projectId: _projectId,
  collectionId: _collectionId,
}: ResearchPageProps) {
  const {
    report,
    loading,
    error,
    runResearch,
    clear,
  } = useResearch();

  async function handleResearch(query: string) {
    const question = query.trim();

    if (!question || question.length < 3) {
      return;
    }

    try {
      await runResearch({
        question,
        depth: "medium",
        include_papers: true,
        include_github: true,
        include_docs: true,
      });
    } catch {
      // useResearch stores the error in its own state.
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col bg-background">
      {/* Header */}
      <header className="shrink-0 border-b">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border">
              <Brain className="h-5 w-5" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold">
                  Research Assistant
                </h1>

                <span className="rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider">
                  AI Assistant
                </span>
              </div>

              <p className="text-xs text-muted-foreground">
                Ask · Research · Synthesize · Verify
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden items-center gap-2 rounded-lg border px-3 py-2 text-[10px] text-muted-foreground md:flex">
              <Sparkles className="h-3 w-3" />
              Assistant
            </div>

            <div className="hidden items-center gap-2 rounded-lg border px-3 py-2 text-[10px] text-muted-foreground lg:flex">
              <ShieldCheck className="h-3 w-3" />
              Verified
            </div>

            {report && (
              <button
                type="button"
                onClick={clear}
                disabled={loading}
                className="flex h-9 items-center gap-2 rounded-lg border px-3 text-xs transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
              >
                <RotateCcw className="h-3.5 w-3.5" />

                <span className="hidden sm:inline">
                  New Research
                </span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-6 py-6">
          {report ? (
            <ResearchReportView
              report={report}
            />
          ) : (
            <ResearchWelcome
              onExample={handleResearch}
              loading={loading}
            />
          )}

          {error && (
            <ErrorPanel
              message={error}
            />
          )}
        </div>
      </main>

      {/* Input */}
      <ResearchInput
        loading={loading}
        onSubmit={handleResearch}
      />
    </div>
  );
}

function ResearchReportView({
  report,
}: {
  report: ResearchReport;
}) {
  const sections = report.sections ?? [];
  const evidence = report.evidence ?? [];
  const sources = report.sources ?? [];
  const citations = report.citations ?? [];

  return (
    <div className="space-y-6">
      {/* Report header */}
      <div className="rounded-2xl border bg-muted/20 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Research Report
            </p>

            <h2 className="mt-2 text-xl font-semibold leading-7">
              {report.title}
            </h2>
          </div>

          {report.status && (
            <span className="rounded-full border px-3 py-1 text-[10px] font-medium uppercase tracking-wider">
              {report.status}
            </span>
          )}
        </div>
      </div>

      {/* Executive summary */}
      <section className="rounded-2xl border p-6">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4" />

          <h3 className="text-sm font-semibold">
            Executive Summary
          </h3>
        </div>

        <p className="whitespace-pre-wrap text-sm leading-7 text-muted-foreground">
          {report.summary}
        </p>
      </section>

      {/* Research sections */}
      {sections.length > 0 && (
        <section className="space-y-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Findings
            </p>

            <h3 className="mt-1 text-lg font-semibold">
              Research Analysis
            </h3>
          </div>

          {sections.map((section, index) => (
            <article
              key={`${section.title}-${index}`}
              className="rounded-2xl border p-6"
            >
              <h4 className="text-base font-semibold">
                {section.title}
              </h4>

              <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">
                {section.content}
              </p>

              {section.evidence_ids?.length > 0 && (
                <div className="mt-4">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Supporting Evidence
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2">
                    {section.evidence_ids.map(
                      (evidenceId) => (
                        <span
                          key={evidenceId}
                          className="rounded-md border px-2 py-1 text-[10px] text-muted-foreground"
                        >
                          {evidenceId}
                        </span>
                      ),
                    )}
                  </div>
                </div>
              )}
            </article>
          ))}
        </section>
      )}

      {/* Comparison */}
      {report.comparison && (
        <ComparisonSection
          comparison={report.comparison}
        />
      )}

      {/* Evidence */}
      {evidence.length > 0 && (
        <section className="rounded-2xl border p-6">
          <div className="mb-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Evidence
            </p>

            <h3 className="mt-1 text-lg font-semibold">
              Supporting Evidence
            </h3>
          </div>

          <div className="space-y-4">
            {evidence.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border bg-muted/10 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {item.claim}
                  </p>

                  <div className="flex gap-2">
                    <span className="rounded-md border px-2 py-1 text-[10px] text-muted-foreground">
                      Confidence:{" "}
                      {Math.round(
                        item.confidence * 100,
                      )}
                      %
                    </span>

                    <span className="rounded-md border px-2 py-1 text-[10px] text-muted-foreground">
                      Relevance:{" "}
                      {item.relevance_score.toFixed(2)}
                    </span>
                  </div>
                </div>

                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                  {item.supporting_text}
                </p>

                <p className="mt-3 text-[10px] text-muted-foreground">
                  Source: {item.source_id}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <section className="rounded-2xl border p-6">
          <div className="mb-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Sources
            </p>

            <h3 className="mt-1 text-lg font-semibold">
              Research Sources
            </h3>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {sources.map((source) => (
              <article
                key={source.id}
                className="rounded-xl border p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h4 className="truncate text-sm font-medium">
                      {source.title}
                    </h4>

                    <p className="mt-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                      {source.source_type}
                    </p>
                  </div>
                </div>

                {source.authors?.length > 0 && (
                  <p className="mt-3 text-xs text-muted-foreground">
                    {source.authors.join(", ")}
                  </p>
                )}

                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 block truncate text-xs underline underline-offset-2"
                  >
                    {source.url}
                  </a>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Citations */}
      {citations.length > 0 && (
        <section className="rounded-2xl border p-6">
          <div className="mb-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Citations
            </p>

            <h3 className="mt-1 text-lg font-semibold">
              References
            </h3>
          </div>

          <div className="space-y-3">
            {citations.map((citation) => (
              <article
                key={citation.id}
                className="rounded-xl border p-4"
              >
                <p className="text-sm leading-6">
                  {citation.citation_text}
                </p>

                {citation.url && (
                  <a
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 block truncate text-xs underline underline-offset-2"
                  >
                    {citation.url}
                  </a>
                )}
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function ComparisonSection({
  comparison,
}: {
  comparison: NonNullable<
    ResearchReport["comparison"]
  >;
}) {
  return (
    <section className="rounded-2xl border p-6">
      <div className="mb-4">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Comparison
        </p>

        <h3 className="mt-1 text-lg font-semibold">
          {comparison.topic}
        </h3>
      </div>

      {comparison.criteria.length > 0 && (
        <div className="mb-5 flex flex-wrap gap-2">
          {comparison.criteria.map(
            (criterion) => (
              <span
                key={criterion}
                className="rounded-md border px-2 py-1 text-[10px] text-muted-foreground"
              >
                {criterion}
              </span>
            ),
          )}
        </div>
      )}

      {comparison.comparison_table.length > 0 && (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full min-w-[600px] text-sm">
            <tbody>
              {comparison.comparison_table.map(
                (row, index) => (
                  <tr
                    key={index}
                    className="border-b last:border-b-0"
                  >
                    {Object.entries(row).map(
                      ([key, value]) => (
                        <td
                          key={key}
                          className="p-3 align-top"
                        >
                          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                            {key}
                          </div>

                          <div className="mt-1 leading-6">
                            {String(value)}
                          </div>
                        </td>
                      ),
                    )}
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ResearchWelcome({
  onExample,
  loading,
}: {
  onExample: (query: string) => void;
  loading: boolean;
}) {
  const examples = [
    "What are the main findings across the research papers in my knowledge base?",
    "Compare the approaches used by the papers and identify their trade-offs.",
    "What evidence supports the main conclusions of these papers?",
    "What research gaps and emerging directions exist in this field?",
  ];

  return (
    <div className="flex min-h-[620px] flex-col items-center justify-center text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border">
        <Brain className="h-8 w-8" />
      </div>

      <h2 className="mt-6 text-2xl font-semibold">
        Research Assistant
      </h2>

      <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
        Ask a research question and the Assistant will investigate
        it using your research knowledge base and available research
        sources, then synthesize and verify the answer.
      </p>

      <div className="mt-8 grid w-full max-w-3xl gap-2 sm:grid-cols-2">
        {examples.map((example) => (
          <button
            key={example}
            type="button"
            disabled={loading}
            onClick={() => onExample(example)}
            className="rounded-xl border p-4 text-left text-sm transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}

function ErrorPanel({
  message,
}: {
  message: string;
}) {
  return (
    <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
      <div className="flex gap-3">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />

        <div className="flex-1">
          <p className="text-sm font-medium text-destructive">
            Research execution failed
          </p>

          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            {message}
          </p>
        </div>

        <X className="h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  );
}