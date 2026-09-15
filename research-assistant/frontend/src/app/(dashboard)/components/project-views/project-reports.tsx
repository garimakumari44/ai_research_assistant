'use client';

import { useState } from 'react';
import { SectionLabel, Divider } from '../../components/primitives';
import { cn } from '../lib/utils';
import { useReport } from '@/reports/hooks/use-report';


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

  const [active, setActive] = useState<string | null>(null);

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

  const sections = report.sections ?? [];

  const activeSection =
    sections.find((section) => section.id === active) ??
    sections[0];

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
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActive(section.id)}
                className={cn(
                  'block w-full text-left rounded-sm px-2.5 py-1.5 text-[12px] transition-colors',
                  activeSection?.id === section.id
                    ? 'text-primary-soft bg-primary/5'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {section.title}
              </button>
            ))}
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

          <Divider className="my-8" />

          <div className="text-[11px] text-faint font-mono-tech">
            {report.paperCount ?? 0} papers cited ·{' '}
            {report.evidenceCount ?? 0} evidence units
            {report.generatedAt &&
              ` · Generated ${new Date(report.generatedAt).toLocaleString()}`}
          </div>
        </div>
      </div>
    </div>
  );
}