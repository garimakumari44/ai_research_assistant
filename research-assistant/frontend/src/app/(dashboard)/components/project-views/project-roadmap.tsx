'use client';

import { SectionLabel } from '../../components/primitives';
import { cn } from '../lib/utils';
import { useResearchRoadmap } from '@/frontier/hooks/use-research-roadmap';


const typeColors: Record<string, string> = {
  gap: 'text-warning',
  question: 'text-primary-soft',
  hypothesis: 'text-primary-soft',
  methodology: 'text-success',
  dataset: 'text-success',
  baseline: 'text-muted-foreground',
  experiment: 'text-primary',
  evaluation: 'text-warning',
  contribution: 'text-success',
};

export function ProjectRoadmap({
  projectId,
}: {
  projectId: string;
}) {
  const {
    data: roadmap,
    isLoading,
    isError,
    refetch,
  } = useResearchRoadmap(projectId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="h-5 w-40 bg-surface animate-pulse rounded mb-6" />
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-20 bg-surface animate-pulse rounded"
            />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-3xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load research roadmap.
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

  const steps = roadmap?.steps ?? [];

  return (
    <div className="mx-auto max-w-3xl">
      <SectionLabel>
        Research Roadmap
      </SectionLabel>

      <div className="relative">
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-border" />

        <div>
          {steps.map((step, index) => (
            <div
              key={step.id}
              className="relative pl-10 pb-8 last:pb-0 group"
            >
              <div
                className={cn(
                  'absolute left-0 top-1 flex h-6 w-6 items-center justify-center rounded-full border bg-elevated',
                  index === 0
                    ? 'border-primary'
                    : 'border-strong-border group-hover:border-primary',
                )}
              >
                <div
                  className={cn(
                    'h-1.5 w-1.5 rounded-full',
                    index === 0
                      ? 'bg-primary'
                      : 'bg-faint group-hover:bg-primary',
                  )}
                />
              </div>

              <div className="rounded-md border border-border bg-surface p-4 hover:border-strong-border transition-colors">
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className={cn(
                      'font-mono-tech text-[10px] uppercase tracking-wider',
                      typeColors[step.type] ??
                        'text-muted-foreground',
                    )}
                  >
                    {step.label}
                  </span>

                  <span className="font-mono-tech text-[10px] text-faint">
                    · {String(index + 1).padStart(2, '0')}/
                    {steps.length}
                  </span>
                </div>

                <p className="text-[13px] text-foreground leading-relaxed">
                  {step.value}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-border flex items-center gap-2">
        <button className="rounded-md border border-primary bg-primary/10 px-3 py-1.5 text-[12px] text-primary-soft hover:bg-primary/20">
          Generate report from roadmap
        </button>

        <button className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground">
          Export
        </button>
      </div>
    </div>
  );
}