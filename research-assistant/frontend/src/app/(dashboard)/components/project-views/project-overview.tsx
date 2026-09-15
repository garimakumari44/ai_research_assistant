'use client';

import {
  SectionLabel,
  MetricLabel,
} from '../../components/primitives';
import { useProjectOverview } from '@/projects/hooks/use-project-overview';

export function ProjectOverview({
  projectId,
}: {
  projectId: string;
}) {
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useProjectOverview(projectId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="h-8 w-64 bg-surface animate-pulse rounded" />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-24 bg-surface animate-pulse rounded"
            />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load project overview.
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

  const currentFrontier =
    typeof data.currentFrontier === 'string'
      ? data.currentFrontier
      : 'No current frontier identified.';

  return (
    <div className="mx-auto max-w-5xl">
      <SectionLabel>
        Research Overview
      </SectionLabel>

      <div className="mb-8">
        <h1 className="text-xl font-medium text-foreground">
          {data.name}
        </h1>

        {data.description && (
          <p className="mt-2 max-w-3xl text-[13px] text-muted-foreground leading-relaxed">
            {data.description}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <MetricCard
          label="Papers"
          value={data.paperCount}
        />

        <MetricCard
          label="Evidence"
          value={data.evidenceCount}
        />

        <MetricCard
          label="Research Gaps"
          value={data.gapCount}
        />

        <MetricCard
          label="Hypotheses"
          value={data.hypothesisCount}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="rounded-lg border border-border bg-surface p-5">
          <SectionLabel>
            Current Frontier
          </SectionLabel>

          <p className="text-[14px] text-foreground leading-relaxed">
            {currentFrontier}
          </p>
        </section>

        <section className="rounded-lg border border-border bg-surface p-5">
          <SectionLabel>
            Primary Research Question
          </SectionLabel>

          <p className="text-[14px] text-foreground leading-relaxed">
            {data.researchQuestion ||
              'No research question defined.'}
          </p>
        </section>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value?: number | string | null;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <MetricLabel>
        {label}
      </MetricLabel>

      <p className="font-mono-tech text-2xl text-secondary-foreground tabular-nums mt-1">
        {value ?? 0}
      </p>
    </div>
  );
}