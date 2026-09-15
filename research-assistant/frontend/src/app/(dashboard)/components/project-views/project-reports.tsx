'use client';

import { useMemo, useState } from 'react';
import {
  SectionLabel,
  Divider,
} from '../../components/primitives';
import { cn } from '../lib/utils';
import { useReport } from '@/reports/hooks/use-report';
import type { ReportContent } from '@/reports/types';

interface ReportSection {
  id: string;
  title: string;
  content: string;
}

function formatValue(value: unknown): string {
  if (typeof value === 'string') {
    return value;
  }

  if (
    value === null ||
    value === undefined
  ) {
    return '';
  }

  if (
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => formatValue(item))
      .filter(Boolean)
      .map((item) => `• ${item}`)
      .join('\n');
  }

  if (typeof value === 'object') {
    const item =
      value as Record<string, unknown>;

    const claim =
      typeof item.claim === 'string'
        ? item.claim
        : '';

    const evidence =
      typeof item.evidence === 'string'
        ? item.evidence
        : typeof item.quote === 'string'
          ? item.quote
          : '';

    if (claim || evidence) {
      return [claim, evidence]
        .filter(Boolean)
        .join('\n\n');
    }

    try {
      return JSON.stringify(
        value,
        null,
        2,
      );
    } catch {
      return '';
    }
  }

  return String(value);
}

function buildSections(
  content:
    | ReportContent
    | null
    | undefined,
): ReportSection[] {
  if (!content) {
    return [];
  }

  const sections: ReportSection[] = [];

  const addSection = (
    id: string,
    title: string,
    value: unknown,
  ) => {
    const text = formatValue(value);

    if (text.trim()) {
      sections.push({
        id,
        title,
        content: text,
      });
    }
  };

  addSection(
    'executive-summary',
    'Executive Summary',
    content.executive_summary,
  );

  addSection(
    'key-findings',
    'Key Findings',
    content.key_findings,
  );

  addSection(
    'methodology',
    'Methodology',
    content.methodology,
  );

  addSection(
    'evidence-synthesis',
    'Evidence Synthesis',
    content.evidence_synthesis,
  );

  addSection(
    'supporting-evidence',
    'Supporting Evidence',
    content.supporting_evidence,
  );

  addSection(
    'contradictions',
    'Contradictions',
    content.contradictions,
  );

  addSection(
    'research-gaps',
    'Research Gaps',
    content.research_gaps,
  );

  addSection(
    'emerging-trends',
    'Emerging Trends',
    content.emerging_trends,
  );

  addSection(
    'future-directions',
    'Future Directions',
    content.future_directions,
  );

  addSection(
    'conclusion',
    'Conclusion',
    content.conclusion,
  );

  return sections;
}

export function ProjectReports({
  projectId,
}: {
  projectId: string;
}) {
  const {
    data: report,
    isLoading,
    isError,
    refetch,
  } = useReport(projectId);

  const [active, setActive] =
    useState<string | null>(null);

  const sections = useMemo(
    () =>
      buildSections(
        report?.content,
      ),
    [report],
  );

  const activeSection =
    sections.find(
      (section) =>
        section.id === active,
    ) ?? sections[0];

  const paperCount =
    report?.evidence?.length ?? 0;

  const evidenceCount =
    report?.evidence?.length ?? 0;

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl">
        <div className="h-6 w-72 bg-surface rounded animate-pulse mb-6" />

        <div className="h-96 bg-surface rounded animate-pulse" />
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load the project report.
        </p>

        <button
          onClick={() => refetch()}
          className="border border-border rounded-md px-3 py-1.5 text-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <SectionLabel className="mb-0">
          Report · {report.title}
        </SectionLabel>

        <div className="flex items-center gap-2">
          <button className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground">
            Edit
          </button>

          <button className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground">
            Regenerate
          </button>

          <button className="rounded-md border border-primary bg-primary/10 px-3 py-1.5 text-[12px] text-primary-soft hover:bg-primary/20">
            Export
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-8">
        <nav className="lg:sticky lg:top-0 lg:self-start">
          <div className="space-y-0.5">
            {sections.map(
              (section) => (
                <button
                  key={section.id}
                  onClick={() =>
                    setActive(
                      section.id,
                    )
                  }
                  className={cn(
                    'block w-full text-left rounded-sm px-2.5 py-1.5 text-[12px] transition-colors',
                    activeSection?.id ===
                      section.id
                      ? 'text-primary-soft bg-primary/5'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {section.title}
                </button>
              ),
            )}
          </div>
        </nav>

        <div className="max-w-2xl">
          {activeSection && (
            <>
              <h2 className="text-[18px] font-medium text-foreground mb-4">
                {activeSection.title}
              </h2>

              <div className="text-[14px] text-secondary-foreground leading-relaxed whitespace-pre-wrap">
                {activeSection.content}
              </div>
            </>
          )}

          {!activeSection &&
            report.summary && (
              <>
                <h2 className="text-[18px] font-medium text-foreground mb-4">
                  Summary
                </h2>

                <div className="text-[14px] text-secondary-foreground leading-relaxed whitespace-pre-wrap">
                  {formatValue(
                    report.summary,
                  )}
                </div>
              </>
            )}

          <Divider className="my-8" />

          <div className="text-[11px] text-faint font-mono-tech">
            {paperCount} papers cited ·{' '}
            {evidenceCount} evidence units
            {report.created_at &&
              ` · Generated ${new Date(
                report.created_at,
              ).toLocaleString()}`}
          </div>
        </div>
      </div>
    </div>
  );
}