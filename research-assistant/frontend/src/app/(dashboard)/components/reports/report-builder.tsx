"use client";

import {
  ArrowLeft,
  Check,
  FileText,
  Loader2,
  Plus,
  Save,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

import {
  ReportSection,
  ReportSectionData,
} from "./report-section";

interface ReportBuilderProps {
  initialTitle?: string;
  initialDescription?: string;
  initialSections?: ReportSectionData[];
  saving?: boolean;
  generating?: boolean;
  onBack?: () => void;
  onSave?: (report: {
    title: string;
    description: string;
    sections: ReportSectionData[];
  }) => void;
  onGenerate?: (report: {
    title: string;
    description: string;
    sections: ReportSectionData[];
  }) => void;
}

function createSection(order: number): ReportSectionData {
  return {
    id: `section-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2)}`,
    title: `Section ${order}`,
    content: "",
    order,
    citations: 0,
  };
}

export function ReportBuilder({
  initialTitle = "",
  initialDescription = "",
  initialSections = [],
  saving = false,
  generating = false,
  onBack,
  onSave,
  onGenerate,
}: ReportBuilderProps) {
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(
    initialDescription,
  );

  const [sections, setSections] = useState<ReportSectionData[]>(
    initialSections,
  );

  const updateSection = (
    updatedSection: ReportSectionData,
  ) => {
    setSections((current) =>
      current.map((section) =>
        section.id === updatedSection.id
          ? updatedSection
          : section,
      ),
    );
  };

  const deleteSection = (section: ReportSectionData) => {
    setSections((current) =>
      current
        .filter((item) => item.id !== section.id)
        .map((item, index) => ({
          ...item,
          order: index + 1,
        })),
    );
  };

  const addSection = () => {
    setSections((current) => [
      ...current,
      createSection(current.length + 1),
    ]);
  };

  const addSectionAfter = (section: ReportSectionData) => {
    setSections((current) => {
      const index = current.findIndex(
        (item) => item.id === section.id,
      );

      const newSection = createSection(index + 2);

      const next = [...current];

      next.splice(index + 1, 0, newSection);

      return next.map((item, itemIndex) => ({
        ...item,
        order: itemIndex + 1,
      }));
    });
  };

  const payload = {
    title: title.trim(),
    description: description.trim(),
    sections,
  };

  return (
    <section className="flex h-full flex-col bg-zinc-950">
      <header className="flex items-center gap-3 border-b border-zinc-800 px-6 py-3">
        <button
          type="button"
          onClick={onBack}
          className="rounded-md p-2 text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-200"
          aria-label="Back"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>

        <div className="flex min-w-0 flex-1 items-center gap-2">
          <FileText className="h-4 w-4 text-zinc-500" />

          <span className="text-sm font-medium text-zinc-300">
            Report Builder
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={generating || saving}
            onClick={() => onGenerate?.(payload)}
            className="inline-flex items-center gap-2 rounded-md border border-zinc-800 px-3 py-2 text-xs font-medium text-zinc-300 transition hover:bg-zinc-900 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}

            Generate
          </button>

          <button
            type="button"
            disabled={saving || generating || !title.trim()}
            onClick={() => onSave?.(payload)}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}

            Save
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-6 py-10">
          <div className="mb-8">
            <label
              htmlFor="report-title"
              className="mb-2 block text-xs font-medium uppercase tracking-wider text-zinc-600"
            >
              Report title
            </label>

            <input
              id="report-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Enter report title..."
              className="w-full bg-transparent text-3xl font-semibold tracking-tight text-zinc-100 outline-none placeholder:text-zinc-700"
            />

            <textarea
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              rows={2}
              placeholder="Add a short description..."
              className="mt-3 w-full resize-none bg-transparent text-sm leading-6 text-zinc-500 outline-none placeholder:text-zinc-700"
            />
          </div>

          <div className="space-y-4">
            {sections.length === 0 ? (
              <div className="rounded-lg border border-dashed border-zinc-800 px-6 py-12 text-center">
                <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full border border-zinc-800 bg-zinc-900">
                  <FileText className="h-5 w-5 text-zinc-600" />
                </div>

                <h2 className="text-sm font-medium text-zinc-300">
                  Start your report
                </h2>

                <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-zinc-600">
                  Add sections manually or generate a research report
                  from your retrieved evidence.
                </p>

                <button
                  type="button"
                  onClick={addSection}
                  className="mt-4 inline-flex items-center gap-2 rounded-md border border-zinc-700 px-3 py-2 text-xs text-zinc-300 transition hover:bg-zinc-900"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add first section
                </button>
              </div>
            ) : (
              sections.map((section) => (
                <ReportSection
                  key={section.id}
                  section={section}
                  editable
                  onChange={updateSection}
                  onDelete={deleteSection}
                  onAddAfter={addSectionAfter}
                />
              ))
            )}
          </div>

          {sections.length > 0 && (
            <button
              type="button"
              onClick={addSection}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-800 py-3 text-xs text-zinc-600 transition hover:border-zinc-700 hover:bg-zinc-900/40 hover:text-zinc-400"
            >
              <Plus className="h-3.5 w-3.5" />
              Add section
            </button>
          )}

          <div className="mt-8 flex items-center justify-end gap-2 text-xs text-zinc-600">
            <Check className="h-3.5 w-3.5" />
            {sections.length}{" "}
            {sections.length === 1 ? "section" : "sections"}
          </div>
        </div>
      </main>
    </section>
  );
}