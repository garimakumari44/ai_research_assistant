
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  FileBarChart,
  FileText,
  Loader2,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";

import {
  useGenerateReport,
  useReports,
} from "@/reports/hooks/use-reports";

import { useReport } from "@/reports/hooks/use-report";

import type {
  Report,
  ReportContent,
  ReportEvidence,
} from "@/reports/types";

import {
  SectionLabel,
  Divider,
  TrustTag,
} from "../components/primitives";

import { cn } from "./lib/utils";

/* ==========================================================================
   HELPERS
   ========================================================================== */

function getEvidenceId(
  evidence: ReportEvidence,
  index: number,
): string {
  return (
    evidence.chunk_id?.toString() ??
    evidence.paper_id?.toString() ??
    evidence.citation_key ??
    `evidence-${index}`
  );
}

function getEvidenceTitle(
  evidence: ReportEvidence,
): string {
  return (
    evidence.title ??
    evidence.citation_key ??
    evidence.source ??
    "Untitled source"
  );
}

function getEvidenceContext(
  evidence: ReportEvidence,
): string {
  return (
    evidence.quote ??
    evidence.evidence ??
    evidence.supporting_text ??
    ""
  );
}

function getEvidenceDocumentId(
  evidence: ReportEvidence,
): string | null {
  if (
    evidence.paper_id !== null &&
    evidence.paper_id !== undefined
  ) {
    return String(evidence.paper_id);
  }

  if (
    evidence.source_id !== null &&
    evidence.source_id !== undefined
  ) {
    return String(evidence.source_id);
  }

  return null;
}

function getEvidenceScore(
  evidence: ReportEvidence,
): number {
  const value = Number(
    evidence.relevance_score ?? 0,
  );

  if (!Number.isFinite(value)) {
    return 0;
  }

  if (value <= 1) {
    return Math.round(value * 100);
  }

  return Math.round(
    Math.min(value, 100),
  );
}

function formatDate(
  value?: string | null,
): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  );
}

function formatDateTime(
  value?: string | null,
): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  );
}

/* ==========================================================================
   REPORT CONTENT NORMALIZATION
   ========================================================================== */

/**
 * The reports API can return either plain strings or structured
 * evidence/claim objects.
 *
 * React cannot render an object directly:
 *
 *   {item}
 *
 * when item is:
 *
 *   {
 *     id,
 *     claim,
 *     source_id,
 *     confidence,
 *     relevance_score,
 *     supporting_text
 *   }
 *
 * These helpers normalize those values into displayable strings.
 */

function formatReportItem(
  item: unknown,
): string {
  if (
    typeof item === "string"
  ) {
    return item;
  }

  if (
    item === null ||
    item === undefined
  ) {
    return "";
  }

  if (
    typeof item === "number" ||
    typeof item === "boolean"
  ) {
    return String(item);
  }

  if (
    typeof item === "object"
  ) {
    const value =
      item as Record<
        string,
        unknown
      >;

    const claim =
      typeof value.claim ===
      "string"
        ? value.claim
        : "";

    const supportingText =
      typeof value.supporting_text ===
      "string"
        ? value.supporting_text
        : typeof value.evidence ===
            "string"
          ? value.evidence
          : typeof value.quote ===
              "string"
            ? value.quote
            : "";

    const confidence =
      value.confidence !==
        null &&
      value.confidence !==
        undefined
        ? Number(
            value.confidence,
          )
        : null;

    const relevanceScore =
      value.relevance_score !==
        null &&
      value.relevance_score !==
        undefined
        ? Number(
            value.relevance_score,
          )
        : null;

    const sourceId =
      value.source_id !==
        null &&
      value.source_id !==
        undefined
        ? String(
            value.source_id,
          )
        : "";

    const parts: string[] =
      [];

    if (claim) {
      parts.push(claim);
    }

    if (supportingText) {
      parts.push(
        `Supporting evidence: ${supportingText}`,
      );
    }

    if (
      confidence !== null &&
      Number.isFinite(
        confidence,
      )
    ) {
      parts.push(
        `Confidence: ${
          confidence <= 1
            ? Math.round(
                confidence * 100,
              )
            : Math.round(
                confidence,
              )
        }%`,
      );
    }

    if (
      relevanceScore !==
        null &&
      Number.isFinite(
        relevanceScore,
      )
    ) {
      parts.push(
        `Relevance: ${
          relevanceScore <= 1
            ? Math.round(
                relevanceScore * 100,
              )
            : Math.round(
                relevanceScore,
              )
        }%`,
      );
    }

    if (sourceId) {
      parts.push(
        `Source: ${sourceId}`,
      );
    }

    if (
      parts.length > 0
    ) {
      return parts.join("\n");
    }

    /*
     * Last-resort fallback.
     *
     * This guarantees that an unexpected object can never reach
     * React as a child.
     */
    try {
      return JSON.stringify(
        item,
      );
    } catch {
      return "";
    }
  }

  return String(item);
}

function formatReportList(
  items: unknown[],
): string {
  return items
    .map((item) =>
      formatReportItem(item),
    )
    .filter(Boolean)
    .map(
      (item) => `• ${item}`,
    )
    .join("\n");
}

/* ==========================================================================
   CONTENT → SECTIONS
   ========================================================================== */

function buildReportSections(
  content:
    | ReportContent
    | null
    | undefined,
) {
  if (!content) {
    return [];
  }

  const sections: Array<{
    id: string;
    title: string;
    content: string;
    order: number;
  }> = [];

  let order = 0;

  /* ------------------------------------------------------------------------
     Executive Summary
     ------------------------------------------------------------------------ */

  if (
    content.executive_summary
  ) {
    sections.push({
      id: "executive-summary",
      title:
        "Executive Summary",
      content:
        formatReportItem(
          content.executive_summary,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Key Findings
     ------------------------------------------------------------------------ */

  if (
    Array.isArray(
      content.key_findings,
    ) &&
    content.key_findings.length >
      0
  ) {
    sections.push({
      id: "key-findings",
      title: "Key Findings",
      content:
        formatReportList(
          content.key_findings,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Methodology
     ------------------------------------------------------------------------ */

  if (
    content.methodology
  ) {
    sections.push({
      id: "methodology",
      title: "Methodology",
      content:
        formatReportItem(
          content.methodology,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Evidence Synthesis
     ------------------------------------------------------------------------ */

  if (
    content.evidence_synthesis
  ) {
    sections.push({
      id: "evidence-synthesis",
      title:
        "Evidence Synthesis",
      content:
        formatReportItem(
          content.evidence_synthesis,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Supporting Evidence
     ------------------------------------------------------------------------ */

  if (
    content.supporting_evidence
  ) {
    sections.push({
      id: "supporting-evidence",
      title:
        "Supporting Evidence",
      content:
        formatReportItem(
          content.supporting_evidence,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Contradictions
     ------------------------------------------------------------------------ */

  if (
    Array.isArray(
      content.contradictions,
    ) &&
    content.contradictions
      .length > 0
  ) {
    sections.push({
      id: "contradictions",
      title:
        "Contradictions",
      content:
        formatReportList(
          content.contradictions,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Research Gaps
     ------------------------------------------------------------------------ */

  if (
    Array.isArray(
      content.research_gaps,
    ) &&
    content.research_gaps
      .length > 0
  ) {
    sections.push({
      id: "research-gaps",
      title:
        "Research Gaps",
      content:
        formatReportList(
          content.research_gaps,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Emerging Trends
     ------------------------------------------------------------------------ */

  if (
    Array.isArray(
      content.emerging_trends,
    ) &&
    content.emerging_trends
      .length > 0
  ) {
    sections.push({
      id: "emerging-trends",
      title:
        "Emerging Trends",
      content:
        formatReportList(
          content.emerging_trends,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Future Directions
     ------------------------------------------------------------------------ */

  if (
    Array.isArray(
      content.future_directions,
    ) &&
    content.future_directions
      .length > 0
  ) {
    sections.push({
      id: "future-directions",
      title:
        "Future Directions",
      content:
        formatReportList(
          content.future_directions,
        ),
      order: order++,
    });
  }

  /* ------------------------------------------------------------------------
     Conclusion
     ------------------------------------------------------------------------ */

  if (
    content.conclusion
  ) {
    sections.push({
      id: "conclusion",
      title: "Conclusion",
      content:
        formatReportItem(
          content.conclusion,
        ),
      order: order++,
    });
  }

  return sections;
}

/* ==========================================================================
   PAGE
   ========================================================================== */

export function ReportsPage() {
  const [query, setQuery] =
    useState("");

  const [
    selectedReportId,
    setSelectedReportId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    activeSection,
    setActiveSection,
  ] =
    useState<string | null>(
      null,
    );

  /* ------------------------------------------------------------------------
     Queries / mutations
     ------------------------------------------------------------------------ */

  const reportsQuery =
    useReports();

  const reportQuery =
    useReport(
      selectedReportId ??
        undefined,
    );

  const generateReportMutation =
    useGenerateReport();

  /* ------------------------------------------------------------------------
     Reports
     ------------------------------------------------------------------------ */

  const reports =
    useMemo<Report[]>(
      () =>
        reportsQuery.data
          ?.items ?? [],
      [reportsQuery.data],
    );

  /* ------------------------------------------------------------------------
     Automatically select first report
     ------------------------------------------------------------------------ */

  useEffect(() => {
    if (
      !selectedReportId &&
      reports.length > 0
    ) {
      const firstReport =
        reports[0];

      if (
        firstReport?.id
      ) {
        setSelectedReportId(
          String(
            firstReport.id,
          ),
        );
      }
    }
  }, [
    reports,
    selectedReportId,
  ]);

  /* ------------------------------------------------------------------------
     Selected report
     ------------------------------------------------------------------------ */

  const report =
    reportQuery.data ??
    null;

  const reportContent =
    useMemo<ReportContent | null>(
      () => {
        if (
          !report?.content
        ) {
          return null;
        }

        return report.content;
      },
      [report],
    );

  /* ------------------------------------------------------------------------
     Sections
     ------------------------------------------------------------------------ */

  const sections =
    useMemo(
      () =>
        buildReportSections(
          reportContent,
        ),
      [reportContent],
    );

  /* ------------------------------------------------------------------------
     Evidence
     ------------------------------------------------------------------------ */

  const evidence =
    useMemo<ReportEvidence[]>(
      () =>
        Array.isArray(
          report?.evidence,
        )
          ? report.evidence
          : [],
      [report],
    );

  /* ------------------------------------------------------------------------
     Active section
     ------------------------------------------------------------------------ */

  useEffect(() => {
    if (
      sections.length === 0
    ) {
      setActiveSection(
        null,
      );
      return;
    }

    setActiveSection(
      (current) => {
        const exists =
          sections.some(
            (section) =>
              section.id ===
              current,
          );

        return exists
          ? current
          : sections[0].id;
      },
    );
  }, [sections]);

  /* ==========================================================================
     GENERATE REPORT
     ========================================================================== */

  const handleGenerate =
    async () => {
      const trimmed =
        query.trim();

      if (
        !trimmed ||
        generateReportMutation.isPending
      ) {
        return;
      }

      try {
        const generated =
          await generateReportMutation.mutateAsync(
            {
              title: trimmed,
              research_question:
                trimmed,
              paper_ids: [],
              metadata: {
                depth: "deep",
                include_papers:
                  true,
                include_github:
                  true,
                include_docs:
                  true,
              },
            },
          );

        setQuery("");

        setSelectedReportId(
          String(
            generated.id,
          ),
        );

        setActiveSection(
          null,
        );

        await reportsQuery.refetch();
      } catch (error) {
        console.error(
          "Failed to generate report:",
          error,
        );
      }
    };

  /* ==========================================================================
     NAVIGATION
     ========================================================================== */

  const handleSectionClick =
    (
      sectionId: string,
    ) => {
      setActiveSection(
        sectionId,
      );

      window.requestAnimationFrame(
        () => {
          document
            .getElementById(
              sectionId,
            )
            ?.scrollIntoView({
              behavior:
                "smooth",
              block: "start",
            });
        },
      );
    };

  /* ==========================================================================
     PDF
     ========================================================================== */

  const handleDownloadPdf =
    () => {
      if (!report) {
        return;
      }

      document.body.classList.add(
        "printing-report",
      );

      window.setTimeout(() => {
        window.print();

        window.setTimeout(
          () => {
            document.body.classList.remove(
              "printing-report",
            );
          },
          1000,
        );
      }, 100);
    };

  /* ==========================================================================
     REFRESH
     ========================================================================== */

  const handleRefresh =
    async () => {
      if (
        selectedReportId
      ) {
        await reportQuery.refetch();
      } else {
        await reportsQuery.refetch();
      }
    };

  /* ==========================================================================
     STATES
     ========================================================================== */

  const isGenerating =
    generateReportMutation.isPending;

  const isLoading =
    reportsQuery.isLoading ||
    (!!selectedReportId &&
      reportQuery.isLoading);

  const hasError =
    reportsQuery.isError ||
    (!!selectedReportId &&
      reportQuery.isError) ||
    generateReportMutation.isError;

  let errorMessage =
    "The reports service returned an error.";

  if (
    generateReportMutation.isError
  ) {
    errorMessage =
      generateReportMutation.error instanceof
      Error
        ? generateReportMutation
            .error.message
        : errorMessage;
  } else if (
    reportsQuery.isError
  ) {
    errorMessage =
      reportsQuery.error instanceof
      Error
        ? reportsQuery.error.message
        : errorMessage;
  } else if (
    reportQuery.isError
  ) {
    errorMessage =
      reportQuery.error instanceof
      Error
        ? reportQuery.error.message
        : errorMessage;
  }

  /* ==========================================================================
     RENDER
     ========================================================================== */

  return (
    <div
      id="research-report-page"
      className="mx-auto max-w-7xl px-6 py-10 md:px-10"
    >
      {/* =====================================================================
          HEADER
          ===================================================================== */}

      <div className="report-chrome mb-6">
        <div className="mb-2 flex items-center gap-2">
          <FileBarChart className="h-4 w-4 text-primary" />

          <span className="font-mono-tech text-[10px] uppercase tracking-widest text-faint">
            Research Synthesis
          </span>
        </div>

        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-xl font-medium tracking-tight text-foreground">
              Reports
            </h1>

            <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
              Academic document synthesis with
              traceable research evidence.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/explore"
              className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
            >
              <ArrowLeft className="h-3 w-3" />
              Explore
            </Link>

            <button
              type="button"
              onClick={() => {
                void handleRefresh();
              }}
              disabled={
                reportsQuery.isFetching ||
                reportQuery.isFetching ||
                isGenerating
              }
              className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
            >
              {reportsQuery.isFetching ||
              reportQuery.isFetching ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="h-3 w-3" />
              )}

              Refresh
            </button>

            <button
              type="button"
              onClick={
                handleDownloadPdf
              }
              disabled={
                !report ||
                isGenerating
              }
              className="flex items-center gap-1.5 rounded-md border border-primary bg-primary/10 px-3 py-1.5 text-[12px] text-primary-soft transition-colors hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Download className="h-3 w-3" />
              Download PDF
            </button>
          </div>
        </div>
      </div>

      <Divider />

      {/* =====================================================================
          GENERATOR
          ===================================================================== */}

      <section className="report-chrome py-6">
        <SectionLabel>
          Generate Report
        </SectionLabel>

        <div className="mt-4 rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center gap-3">
            <Search className="h-4 w-4 shrink-0 text-faint" />

            <input
              value={query}
              onChange={(event) =>
                setQuery(
                  event.target.value,
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key ===
                    "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();

                  void handleGenerate();
                }
              }}
              disabled={
                isGenerating
              }
              placeholder="Enter a research question, topic, or synthesis request..."
              className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-faint disabled:opacity-50"
            />

            <button
              type="button"
              onClick={() => {
                void handleGenerate();
              }}
              disabled={
                !query.trim() ||
                isGenerating
              }
              className="flex items-center gap-2 rounded-md border border-primary bg-primary/10 px-3 py-2 text-xs text-primary-soft transition-colors hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isGenerating ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Sparkles className="h-3.5 w-3.5" />
              )}

              {isGenerating
                ? "Generating..."
                : "Generate"}
            </button>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-border/60 pt-3">
            <div className="flex items-center gap-2 text-[10px] text-faint">
              <FileText className="h-3 w-3" />

              <span className="font-mono-tech uppercase tracking-wider">
                Evidence-grounded synthesis
              </span>
            </div>

            <div className="flex items-center gap-2">
              <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono-tech text-[9px] text-faint">
                ENTER
              </kbd>

              <span className="text-[10px] text-faint">
                generate
              </span>
            </div>
          </div>
        </div>

        {/* Generation progress */}

        {isGenerating && (
          <div className="mt-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />

              <div>
                <p className="text-[12px] font-medium text-foreground">
                  Building research synthesis
                </p>

                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  Retrieving evidence,
                  synthesizing findings,
                  and preparing the
                  report...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error */}

        {hasError &&
          !isGenerating && (
            <div className="mt-3 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3">
              <p className="text-[12px] font-medium text-foreground">
                Unable to generate or load report
              </p>

              <p className="mt-1 break-words text-[11px] text-muted-foreground">
                {errorMessage}
              </p>
            </div>
          )}
      </section>

      <Divider />

      {/* =====================================================================
          REPORT HISTORY
          ===================================================================== */}

      {reports.length > 0 && (
        <section className="report-chrome py-5">
          <SectionLabel>
            Report History
          </SectionLabel>

          <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
            {reports.map(
              (item) => {
                const id =
                  String(
                    item.id,
                  );

                const selected =
                  selectedReportId ===
                  id;

                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      setSelectedReportId(
                        id,
                      );
                      setActiveSection(
                        null,
                      );
                    }}
                    className={cn(
                      "min-w-[210px] rounded-md border px-3 py-2.5 text-left transition-colors",
                      selected
                        ? "border-primary/40 bg-primary/5"
                        : "border-border bg-surface hover:border-strong-border",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="truncate text-[11px] font-medium text-foreground">
                        {item.title ||
                          "Untitled report"}
                      </p>

                      {selected && (
                        <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-primary" />
                      )}
                    </div>

                    <div className="mt-1.5 flex items-center gap-2">
                      <p className="font-mono-tech text-[9px] text-faint">
                        {formatDate(
                          item.created_at,
                        )}
                      </p>

                      <span className="font-mono-tech text-[9px] uppercase text-faint">
                        {String(
                          item.status ??
                            "",
                        )}
                      </span>
                    </div>
                  </button>
                );
              },
            )}
          </div>
        </section>
      )}

      <Divider />

      {/* =====================================================================
          REPORT
          ===================================================================== */}

      <div id="research-report">
        {/* -------------------------------------------------------------------
            LOADING
            ------------------------------------------------------------------- */}

        {isLoading && (
          <div className="flex items-center justify-center py-24">
            <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading research report...
            </div>
          </div>
        )}

        {/* -------------------------------------------------------------------
            EMPTY
            ------------------------------------------------------------------- */}

        {!isLoading &&
          !report && (
            <div className="py-24 text-center">
              <FileBarChart className="mx-auto h-9 w-9 text-faint" />

              <h2 className="mt-4 text-sm font-medium text-foreground">
                No report selected
              </h2>

              <p className="mx-auto mt-1 max-w-md text-[12px] leading-relaxed text-muted-foreground">
                Generate a research
                report or select an
                existing report from
                your report history.
              </p>
            </div>
          )}

        {/* -------------------------------------------------------------------
            ACTUAL REPORT
            ------------------------------------------------------------------- */}

        {!isLoading &&
          report && (
            <>
              {/* =============================================================
                  REPORT COVER / HEADER
                  ============================================================= */}

              <div className="report-header py-8">
                <div className="border-b border-border pb-7">
                  <div className="flex flex-col gap-5">
                    <div>
                      <span className="font-mono-tech text-[9px] uppercase tracking-[0.2em] text-faint">
                        Research Report
                      </span>

                      <h2 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
                        {report.title ||
                          "Research Report"}
                      </h2>
                    </div>

                    {report.research_question && (
                      <div className="max-w-4xl">
                        <span className="font-mono-tech text-[9px] uppercase tracking-wider text-faint">
                          Research Question
                        </span>

                        <p className="mt-2 text-[14px] leading-7 text-secondary-foreground">
                          {report.research_question}
                        </p>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 font-mono-tech text-[9px] uppercase tracking-wider text-faint">
                      <span>
                        Status:{" "}
                        {String(
                          report.status ??
                            "",
                        )}
                      </span>

                      {report.created_at && (
                        <span>
                          Created{" "}
                          {formatDateTime(
                            report.created_at,
                          )}
                        </span>
                      )}

                      {report.completed_at && (
                        <span>
                          Completed{" "}
                          {formatDateTime(
                            report.completed_at,
                          )}
                        </span>
                      )}

                      <span>
                        {evidence.length}{" "}
                        evidence units
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* =============================================================
                  CONTENT GRID
                  ============================================================= */}

              <div className="grid grid-cols-1 gap-10 lg:grid-cols-[190px_minmax(0,1fr)]">
                {/* -----------------------------------------------------------
                    CONTENTS
                    ----------------------------------------------------------- */}

                <aside className="report-chrome lg:sticky lg:top-4 lg:self-start">
                  <SectionLabel>
                    Contents
                  </SectionLabel>

                  {sections.length ===
                  0 ? (
                    <p className="mt-3 px-2.5 text-[11px] leading-relaxed text-faint">
                      Report content is
                      not available yet.
                    </p>
                  ) : (
                    <div className="mt-3 space-y-0.5">
                      {sections.map(
                        (
                          section,
                        ) => (
                          <button
                            key={
                              section.id
                            }
                            type="button"
                            onClick={() =>
                              handleSectionClick(
                                section.id,
                              )
                            }
                            className={cn(
                              "block w-full rounded-sm px-2.5 py-1.5 text-left text-[11px] leading-5 transition-colors",
                              activeSection ===
                                section.id
                                ? "bg-primary/5 text-primary-soft"
                                : "text-muted-foreground hover:bg-surface hover:text-foreground",
                            )}
                          >
                            <span className="mr-2 font-mono-tech text-[9px] text-faint">
                              {String(
                                section.order +
                                  1,
                              ).padStart(
                                2,
                                "0",
                              )}
                            </span>

                            {section.title}
                          </button>
                        ),
                      )}
                    </div>
                  )}
                </aside>

                {/* -----------------------------------------------------------
                    DOCUMENT
                    ----------------------------------------------------------- */}

                <main className="min-w-0 max-w-4xl">
                  {/* =========================================================
                      SECTIONS
                      ========================================================= */}

                  {sections.map(
                    (section) => (
                      <article
                        key={
                          section.id
                        }
                        id={
                          section.id
                        }
                        className="report-section mb-10 scroll-mt-8 border-b border-border/60 pb-10 last:border-b-0"
                      >
                        <div className="mb-4 flex items-start gap-3">
                          <span className="pt-1 font-mono-tech text-[9px] text-faint">
                            {String(
                              section.order +
                                1,
                            ).padStart(
                              2,
                              "0",
                            )}
                          </span>

                          <h2 className="text-[18px] font-semibold tracking-tight text-foreground">
                            {
                              section.title
                            }
                          </h2>
                        </div>

                        <div className="whitespace-pre-line text-[14px] leading-7 text-secondary-foreground">
                          {
                            section.content
                          }
                        </div>
                      </article>
                    ),
                  )}

                  {/* =========================================================
                      SUMMARY FALLBACK
                      ========================================================= */}

                  {sections.length ===
                    0 &&
                    report.summary && (
                      <article
                        id="summary"
                        className="report-section mb-10 border-b border-border/60 pb-10"
                      >
                        <div className="mb-4 flex items-start gap-3">
                          <span className="pt-1 font-mono-tech text-[9px] text-faint">
                            01
                          </span>

                          <h2 className="text-[18px] font-semibold tracking-tight text-foreground">
                            Summary
                          </h2>
                        </div>

                        <p className="whitespace-pre-line text-[14px] leading-7 text-secondary-foreground">
                          {formatReportItem(
                            report.summary,
                          )}
                        </p>
                      </article>
                    )}

                  {/* =========================================================
                      SUPPORTING EVIDENCE
                      ========================================================= */}

                  {evidence.length >
                    0 && (
                    <section
                      id="evidence"
                      className="report-section mb-10 scroll-mt-8 border-b border-border/60 pb-10"
                    >
                      <div className="mb-5 flex items-start gap-3">
                        <span className="pt-1 font-mono-tech text-[9px] text-faint">
                          E
                        </span>

                        <div>
                          <h2 className="text-[18px] font-semibold tracking-tight text-foreground">
                            Supporting
                            Evidence
                          </h2>

                          <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                            Evidence
                            retrieved
                            and used to
                            ground the
                            synthesis.
                          </p>
                        </div>
                      </div>

                      <div className="space-y-3">
                        {evidence.map(
                          (
                            item,
                            index,
                          ) => {
                            const id =
                              getEvidenceId(
                                item,
                                index,
                              );

                            const title =
                              getEvidenceTitle(
                                item,
                              );

                            const context =
                              getEvidenceContext(
                                item,
                              );

                            const score =
                              getEvidenceScore(
                                item,
                              );

                            const documentId =
                              getEvidenceDocumentId(
                                item,
                              );

                            return (
                              <div
                                key={`${id}-${index}`}
                                className="rounded-lg border border-border bg-surface p-5"
                              >
                                <div className="flex items-start gap-4">
                                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border font-mono-tech text-[9px] text-faint">
                                    {index +
                                      1}
                                  </div>

                                  <div className="min-w-0 flex-1">
                                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                                      <div className="min-w-0">
                                        <h3 className="text-[13px] font-medium leading-5 text-foreground">
                                          {
                                            title
                                          }
                                        </h3>

                                        {item.authors &&
                                          item
                                            .authors
                                            .length >
                                            0 && (
                                            <p className="mt-1 text-[10px] leading-4 text-faint">
                                              {item.authors.join(
                                                ", ",
                                              )}
                                            </p>
                                          )}
                                      </div>

                                      <span className="shrink-0 rounded border border-border px-2 py-1 font-mono-tech text-[9px] text-faint">
                                        {
                                          score
                                        }
                                        % relevance
                                      </span>
                                    </div>

                                    {context && (
                                      <blockquote className="mt-4 border-l-2 border-primary/30 pl-4 text-[12px] leading-6 text-muted-foreground">
                                        {
                                          context
                                        }
                                      </blockquote>
                                    )}

                                    <div className="mt-4 flex flex-wrap items-center gap-3">
                                      <TrustTag category="evidence" />

                                      {item.year && (
                                        <span className="font-mono-tech text-[9px] text-faint">
                                          {
                                            item.year
                                          }
                                        </span>
                                      )}

                                      {item.source && (
                                        <span className="font-mono-tech text-[9px] text-faint">
                                          {
                                            item.source
                                          }
                                        </span>
                                      )}

                                      {documentId && (
                                        <Link
                                          href={`/papers/${encodeURIComponent(
                                            documentId,
                                          )}`}
                                          className="text-[10px] text-primary-soft transition-colors hover:underline"
                                        >
                                          View
                                          source
                                          →
                                        </Link>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          },
                        )}
                      </div>
                    </section>
                  )}

                  {/* =========================================================
                      REFERENCES
                      ========================================================= */}

                  {Array.isArray(
                    reportContent?.references,
                  ) &&
                    reportContent
                      .references
                      .length >
                      0 && (
                      <section
                        id="references"
                        className="report-section mb-10 scroll-mt-8 border-b border-border/60 pb-10"
                      >
                        <div className="mb-5 flex items-start gap-3">
                          <span className="pt-1 font-mono-tech text-[9px] text-faint">
                            R
                          </span>

                          <h2 className="text-[18px] font-semibold tracking-tight text-foreground">
                            References
                          </h2>
                        </div>

                        <ol className="space-y-3">
                          {reportContent.references.map(
                            (
                              reference,
                              index,
                            ) => (
                              <li
                                key={`${index}-${formatReportItem(
                                  reference,
                                )}`}
                                className="flex gap-3 text-[12px] leading-6 text-secondary-foreground"
                              >
                                <span className="font-mono-tech text-[9px] text-faint">
                                  [
                                  {index +
                                    1}
                                  ]
                                </span>

                                <span>
                                  {formatReportItem(
                                    reference,
                                  )}
                                </span>
                              </li>
                            ),
                          )}
                        </ol>
                      </section>
                    )}

                  {/* =========================================================
                      REPORT FOOTER
                      ========================================================= */}

                  <footer className="report-footer pb-12">
                    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 font-mono-tech text-[9px] uppercase tracking-wider text-faint">
                      <span>
                        Evidence
                        grounded
                      </span>

                      <span>
                        {
                          evidence.length
                        }{" "}
                        evidence
                        units
                      </span>

                      {report.created_at && (
                        <span>
                          Created{" "}
                          {formatDate(
                            report.created_at,
                          )}
                        </span>
                      )}

                      {report.completed_at && (
                        <span>
                          Completed{" "}
                          {formatDate(
                            report.completed_at,
                          )}
                        </span>
                      )}
                    </div>
                  </footer>
                </main>
              </div>
            </>
          )}
      </div>
    </div>
  );
}

