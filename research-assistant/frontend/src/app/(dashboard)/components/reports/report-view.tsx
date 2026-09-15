"use client";

import {
  ArrowLeft,
  Calendar,
  Download,
  Edit3,
  FileText,
  Loader2,
  MoreHorizontal,
  Quote,
  Share2,
} from "lucide-react";

import { ReportSection, ReportSectionData } from "./report-section";

export interface ReportData {
  id: string;
  title: string;
  description?: string;
  status?: "draft" | "generating" | "completed" | "failed";
  createdAt?: string;
  updatedAt?: string;
  sections: ReportSectionData[];
  citationCount?: number;
}

interface ReportViewProps {
  report: ReportData;
  loading?: boolean;
  onBack?: () => void;
  onEdit?: () => void;
  onExport?: () => void;
  onShare?: () => void;
}

function formatDate(value?: string) {
  if (!value) return "Unknown";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function ReportView({
  report,
  loading = false,
  onBack,
  onEdit,
  onExport,
  onShare,
}: ReportViewProps) {
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading report...
        </div>
      </div>
    );
  }

  return (
    <section className="flex h-full flex-col">
      <header className="border-b border-zinc-800 bg-zinc-950">
        <div className="flex items-center gap-3 px-6 py-3">
          <button
            type="button"
            onClick={onBack}
            className="rounded-md p-2 text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-200"
            aria-label="Back to reports"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 shrink-0 text-zinc-500" />

              <h1 className="truncate text-sm font-semibold text-zinc-200">
                {report.title}
              </h1>
            </div>
          </div>

          <button
            type="button"
            onClick={onShare}
            className="rounded-md p-2 text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-200"
            aria-label="Share report"
          >
            <Share2 className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={onEdit}
            className="inline-flex items-center gap-2 rounded-md border border-zinc-800 px-3 py-2 text-xs font-medium text-zinc-300 transition hover:bg-zinc-900"
          >
            <Edit3 className="h-3.5 w-3.5" />
            Edit
          </button>

          <button
            type="button"
            onClick={onExport}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-blue-500"
          >
            <Download className="h-3.5 w-3.5" />
            Export
          </button>

          <button
            type="button"
            className="rounded-md p-2 text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-200"
            aria-label="More options"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-6 py-10">
          <div className="mb-8 border-b border-zinc-800 pb-8">
            <h2 className="text-2xl font-semibold tracking-tight text-zinc-100">
              {report.title}
            </h2>

            {report.description && (
              <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-500">
                {report.description}
              </p>
            )}

            <div className="mt-5 flex flex-wrap items-center gap-5 text-xs text-zinc-600">
              {report.updatedAt && (
                <span className="inline-flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  Updated {formatDate(report.updatedAt)}
                </span>
              )}

              <span>
                {report.sections.length}{" "}
                {report.sections.length === 1 ? "section" : "sections"}
              </span>

              {typeof report.citationCount === "number" && (
                <span className="inline-flex items-center gap-1.5">
                  <Quote className="h-3.5 w-3.5" />
                  {report.citationCount} citations
                </span>
              )}

              {report.status && (
                <span className="rounded-full border border-zinc-800 bg-zinc-900 px-2 py-0.5 uppercase tracking-wide text-zinc-500">
                  {report.status}
                </span>
              )}
            </div>
          </div>

          <div className="space-y-4">
            {report.sections.map((section) => (
              <ReportSection
                key={section.id}
                section={section}
                editable={false}
              />
            ))}
          </div>
        </div>
      </main>
    </section>
  );
}