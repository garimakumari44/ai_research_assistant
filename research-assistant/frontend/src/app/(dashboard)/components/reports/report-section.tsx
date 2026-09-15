"use client";

import {
  ChevronDown,
  ChevronUp,
  GripVertical,
  MoreHorizontal,
  Plus,
  Trash2,
} from "lucide-react";
import { useState } from "react";

export interface ReportSectionData {
  id: string;
  title: string;
  content: string;
  order?: number;
  citations?: number;
  collapsed?: boolean;
}

interface ReportSectionProps {
  section: ReportSectionData;
  editable?: boolean;
  onChange?: (section: ReportSectionData) => void;
  onDelete?: (section: ReportSectionData) => void;
  onAddAfter?: (section: ReportSectionData) => void;
}

export function ReportSection({
  section,
  editable = false,
  onChange,
  onDelete,
  onAddAfter,
}: ReportSectionProps) {
  const [collapsed, setCollapsed] = useState(
    section.collapsed ?? false,
  );

  const update = (changes: Partial<ReportSectionData>) => {
    onChange?.({
      ...section,
      ...changes,
    });
  };

  return (
    <article className="group rounded-lg border border-zinc-800 bg-zinc-950/60">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-3">
        {editable && (
          <button
            type="button"
            className="cursor-grab text-zinc-700 hover:text-zinc-500"
            aria-label="Drag section"
          >
            <GripVertical className="h-4 w-4" />
          </button>
        )}

        {editable ? (
          <input
            value={section.title}
            onChange={(event) =>
              update({
                title: event.target.value,
              })
            }
            className="min-w-0 flex-1 bg-transparent text-sm font-semibold text-zinc-200 outline-none"
            placeholder="Section title"
          />
        ) : (
          <h2 className="min-w-0 flex-1 text-sm font-semibold text-zinc-200">
            {section.title}
          </h2>
        )}

        {typeof section.citations === "number" && (
          <span className="text-xs text-zinc-600">
            {section.citations}{" "}
            {section.citations === 1 ? "citation" : "citations"}
          </span>
        )}

        <button
          type="button"
          onClick={() => setCollapsed((value) => !value)}
          className="rounded p-1 text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300"
          aria-label={collapsed ? "Expand section" : "Collapse section"}
        >
          {collapsed ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronUp className="h-4 w-4" />
          )}
        </button>

        {editable && (
          <button
            type="button"
            className="rounded p-1 text-zinc-600 hover:bg-zinc-800 hover:text-zinc-300"
            aria-label="Section actions"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        )}
      </div>

      {!collapsed && (
        <div className="p-4">
          {editable ? (
            <textarea
              value={section.content}
              onChange={(event) =>
                update({
                  content: event.target.value,
                })
              }
              rows={8}
              placeholder="Write or generate the section content..."
              className="w-full resize-y rounded-md border border-zinc-800 bg-zinc-950 p-3 text-sm leading-6 text-zinc-300 outline-none placeholder:text-zinc-700 focus:border-zinc-700"
            />
          ) : (
            <div className="whitespace-pre-wrap text-sm leading-7 text-zinc-400">
              {section.content || "No content available."}
            </div>
          )}

          {editable && (
            <div className="mt-3 flex items-center justify-between">
              <button
                type="button"
                onClick={() => onAddAfter?.(section)}
                className="inline-flex items-center gap-1.5 rounded-md border border-zinc-800 px-2.5 py-1.5 text-xs text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-300"
              >
                <Plus className="h-3.5 w-3.5" />
                Add section
              </button>

              <button
                type="button"
                onClick={() => onDelete?.(section)}
                className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-red-500/70 transition hover:bg-red-500/10 hover:text-red-400"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete
              </button>
            </div>
          )}
        </div>
      )}
    </article>
  );
}