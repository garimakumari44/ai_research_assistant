"use client";

import {
  Check,
  Download,
  FileDown,
  FileText,
  Loader2,
  X,
} from "lucide-react";
import { useState } from "react";

export type ReportExportFormat =
  | "pdf"
  | "docx"
  | "markdown"
  | "txt";

interface ReportExportProps {
  reportId: string;
  reportTitle?: string;
  open?: boolean;
  exporting?: boolean;
  onClose?: () => void;
  onExport?: (format: ReportExportFormat) => void;
}

const formats: Array<{
  value: ReportExportFormat;
  label: string;
  description: string;
}> = [
  {
    value: "pdf",
    label: "PDF",
    description: "Formatted document for sharing and printing.",
  },
  {
    value: "docx",
    label: "Word",
    description: "Editable Microsoft Word document.",
  },
  {
    value: "markdown",
    label: "Markdown",
    description: "Structured Markdown source.",
  },
  {
    value: "txt",
    label: "Plain text",
    description: "Simple text-only version.",
  },
];

export function ReportExport({
  reportId,
  reportTitle,
  open = false,
  exporting = false,
  onClose,
  onExport,
}: ReportExportProps) {
  const [selectedFormat, setSelectedFormat] =
    useState<ReportExportFormat>("pdf");

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-export-title"
        className="w-full max-w-md rounded-lg border border-zinc-800 bg-zinc-950 shadow-2xl"
      >
        <div className="flex items-center gap-3 border-b border-zinc-800 px-5 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900">
            <FileDown className="h-4 w-4 text-zinc-400" />
          </div>

          <div className="min-w-0 flex-1">
            <h2
              id="report-export-title"
              className="text-sm font-semibold text-zinc-200"
            >
              Export report
            </h2>

            <p className="mt-0.5 truncate text-xs text-zinc-600">
              {reportTitle || `Report ${reportId}`}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={exporting}
            className="rounded-md p-2 text-zinc-600 transition hover:bg-zinc-900 hover:text-zinc-300 disabled:opacity-50"
            aria-label="Close export dialog"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-2 p-5">
          {formats.map((format) => {
            const selected = selectedFormat === format.value;

            return (
              <button
                key={format.value}
                type="button"
                onClick={() => setSelectedFormat(format.value)}
                disabled={exporting}
                className={`flex w-full items-center gap-3 rounded-md border p-3 text-left transition ${
                  selected
                    ? "border-blue-500/40 bg-blue-500/5"
                    : "border-zinc-800 bg-zinc-950 hover:border-zinc-700 hover:bg-zinc-900/50"
                }`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${
                    selected
                      ? "border-blue-500/30 bg-blue-500/10"
                      : "border-zinc-800 bg-zinc-900"
                  }`}
                >
                  <FileText
                    className={`h-4 w-4 ${
                      selected
                        ? "text-blue-400"
                        : "text-zinc-500"
                    }`}
                  />
                </div>

                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-zinc-300">
                    {format.label}
                  </p>

                  <p className="mt-0.5 text-xs text-zinc-600">
                    {format.description}
                  </p>
                </div>

                {selected && (
                  <Check className="h-4 w-4 text-blue-400" />
                )}
              </button>
            );
          })}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-zinc-800 px-5 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={exporting}
            className="rounded-md border border-zinc-800 px-3 py-2 text-xs font-medium text-zinc-400 transition hover:bg-zinc-900 hover:text-zinc-200 disabled:opacity-50"
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={exporting}
            onClick={() => onExport?.(selectedFormat)}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {exporting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5" />
            )}

            Export {selectedFormat.toUpperCase()}
          </button>
        </div>
      </div>
    </div>
  );
}