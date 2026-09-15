"use client";

import {
  Calendar,
  ChevronRight,
  FileText,
  MoreHorizontal,
  Plus,
  Search,
} from "lucide-react";
import { useMemo, useState } from "react";

export interface ReportSummary {
  id: string;
  title: string;
  description?: string;
  status?: "draft" | "generating" | "completed" | "failed";
  sectionCount?: number;
  citationCount?: number;
  updatedAt?: string;
  createdAt?: string;
}

interface ReportListProps {
  reports?: ReportSummary[];
  loading?: boolean;
  onCreate?: () => void;
  onSelect?: (report: ReportSummary) => void;
  onDelete?: (report: ReportSummary) => void;
}

const statusStyles: Record<
  NonNullable<ReportSummary["status"]>,
  string
> = {
  draft:
    "border-zinc-700 bg-zinc-900 text-zinc-400",
  generating:
    "border-blue-500/20 bg-blue-500/10 text-blue-400",
  completed:
    "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
  failed:
    "border-red-500/20 bg-red-500/10 text-red-400",
};

function formatDate(value?: string) {
  if (!value) return "No date";

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

export function ReportList({
  reports = [],
  loading = false,
  onCreate,
  onSelect,
  onDelete,
}: ReportListProps) {
  const [search, setSearch] = useState("");

  const filteredReports = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return reports;
    }

    return reports.filter((report) => {
      return (
        report.title.toLowerCase().includes(query) ||
        report.description?.toLowerCase().includes(query)
      );
    });
  }, [reports, search]);

  return (
    <section className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">
            Research Reports
          </h1>

          <p className="mt-1 text-sm text-zinc-500">
            Create, manage, and export research reports.
          </p>
        </div>

        <button
          type="button"
          onClick={onCreate}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-blue-500"
        >
          <Plus className="h-4 w-4" />
          New report
        </button>
      </div>

      <div className="border-b border-zinc-800 px-6 py-3">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search reports..."
            className="w-full rounded-md border border-zinc-800 bg-zinc-950 py-2 pl-9 pr-3 text-sm text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-zinc-700"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="h-24 animate-pulse rounded-lg border border-zinc-800 bg-zinc-900/40"
              />
            ))}
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="flex min-h-[320px] flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full border border-zinc-800 bg-zinc-900 p-3">
              <FileText className="h-6 w-6 text-zinc-500" />
            </div>

            <h2 className="text-sm font-medium text-zinc-300">
              No reports found
            </h2>

            <p className="mt-1 max-w-sm text-sm text-zinc-500">
              Create your first research report to organize findings,
              evidence, and citations.
            </p>

            <button
              type="button"
              onClick={onCreate}
              className="mt-4 inline-flex items-center gap-2 rounded-md border border-zinc-700 px-3 py-2 text-sm text-zinc-300 transition hover:bg-zinc-900"
            >
              <Plus className="h-4 w-4" />
              Create report
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredReports.map((report) => {
              const status = report.status ?? "draft";

              return (
                <div
                  key={report.id}
                  className="group flex items-center gap-4 rounded-lg border border-zinc-800 bg-zinc-950/60 p-4 transition hover:border-zinc-700 hover:bg-zinc-900/50"
                >
                  <button
                    type="button"
                    onClick={() => onSelect?.(report)}
                    className="flex min-w-0 flex-1 items-center gap-4 text-left"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900">
                      <FileText className="h-5 w-5 text-zinc-400" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="truncate text-sm font-medium text-zinc-200">
                          {report.title}
                        </h3>

                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                            statusStyles[status]
                          }`}
                        >
                          {status}
                        </span>
                      </div>

                      {report.description && (
                        <p className="mt-1 truncate text-xs text-zinc-500">
                          {report.description}
                        </p>
                      )}

                      <div className="mt-2 flex items-center gap-4 text-xs text-zinc-600">
                        <span className="inline-flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {formatDate(report.updatedAt ?? report.createdAt)}
                        </span>

                        {typeof report.sectionCount === "number" && (
                          <span>
                            {report.sectionCount}{" "}
                            {report.sectionCount === 1
                              ? "section"
                              : "sections"}
                          </span>
                        )}

                        {typeof report.citationCount === "number" && (
                          <span>
                            {report.citationCount}{" "}
                            {report.citationCount === 1
                              ? "citation"
                              : "citations"}
                          </span>
                        )}
                      </div>
                    </div>

                    <ChevronRight className="h-4 w-4 shrink-0 text-zinc-600 transition group-hover:text-zinc-400" />
                  </button>

                  <button
                    type="button"
                    onClick={() => onDelete?.(report)}
                    aria-label={`Actions for ${report.title}`}
                    className="rounded-md p-2 text-zinc-600 transition hover:bg-zinc-800 hover:text-zinc-300"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}