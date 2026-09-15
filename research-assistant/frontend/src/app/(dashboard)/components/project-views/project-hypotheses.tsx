'use client';

import { useState } from 'react';

import {
  SectionLabel,
  Divider,
  TrustTag,
} from '../../components/primitives';

import { cn } from '../lib/utils';
import { useHypotheses } from '@/frontier/hooks/use-hypotheses';


export function ProjectHypotheses({
  projectId,
}: {
  projectId: string;
}) {
  const [active, setActive] =
    useState(0);

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useHypotheses(projectId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="h-6 w-32 bg-surface animate-pulse rounded" />

        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-20 bg-surface animate-pulse rounded"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-4xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load hypotheses.
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

  const hypotheses = data?.items ?? [];

  if (!hypotheses.length) {
    return (
      <div className="mx-auto max-w-4xl py-16 text-center">
        <p className="text-sm text-muted-foreground">
          No hypotheses have been generated yet.
        </p>
      </div>
    );
  }

  const hypothesis =
    hypotheses[
      Math.min(active, hypotheses.length - 1)
    ];

  return (
    <div className="mx-auto max-w-4xl">
      <SectionLabel>
        Hypotheses
      </SectionLabel>

      <div className="flex flex-col gap-1 mb-6">
        {hypotheses.map(
          (item, index) => (
            <button
              key={item.id}
              onClick={() =>
                setActive(index)
              }
              className={cn(
                'text-left rounded-md border px-4 py-3 transition-colors',
                active === index
                  ? 'border-primary/40 bg-primary/5'
                  : 'border-border bg-surface hover:border-strong-border',
              )}
            >
              <div className="flex items-center gap-3 mb-1">
                <TrustTag category="hypothesis" />

                <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                  {item.id}
                </span>

                <span
                  className={cn(
                    'ml-auto font-mono-tech text-[10px] uppercase tracking-wider',
                    item.status === 'draft'
                      ? 'text-faint'
                      : item.status ===
                          'testing'
                        ? 'text-warning'
                        : item.status ===
                            'validated'
                          ? 'text-success'
                          : 'text-danger',
                  )}
                >
                  {item.status}
                </span>
              </div>

              <p className="text-[13px] leading-relaxed text-foreground">
                {item.statement}
              </p>
            </button>
          ),
        )}
      </div>

      <div className="rounded-lg border border-border bg-surface p-6 space-y-6">
        <section>
          <SectionLabel>
            Statement
          </SectionLabel>

          <p className="text-[14px] text-foreground leading-relaxed">
            {hypothesis.statement}
          </p>
        </section>

        <Divider />

        <DetailSection
          title="Evidence"
          value={hypothesis.evidence}
        />

        <DetailSection
          title="Research Gap"
          value={hypothesis.gap}
        />

        <DetailSection
          title="Why It Matters"
          value={hypothesis.whyItMatters}
        />

        <DetailSection
          title="Potential Contribution"
          value={hypothesis.potentialContribution}
        />

        <Divider />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <DetailSection
            title="Method"
            value={hypothesis.method}
          />

          <DetailSection
            title="Dataset"
            value={hypothesis.dataset}
          />

          <DetailSection
            title="Baseline"
            value={hypothesis.baseline}
          />

          <section>
            <SectionLabel>
              Metrics
            </SectionLabel>

            <div className="flex flex-wrap gap-1.5">
              {hypothesis.metrics?.map(
                (metric) => (
                  <span
                    key={metric}
                    className="font-mono-tech text-[11px] text-secondary-foreground border border-border rounded px-2 py-0.5"
                  >
                    {metric}
                  </span>
                ),
              )}
            </div>
          </section>
        </div>

        <Divider />

        <div className="flex items-center gap-2 flex-wrap">
          <button className="rounded-md border border-primary bg-primary/10 px-3 py-1.5 text-[12px] text-primary-soft hover:bg-primary/20">
            Test hypothesis
          </button>

          <button className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground">
            Build roadmap
          </button>

          <button className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground">
            Find supporting papers
          </button>

          <button className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground">
            Find counter-evidence
          </button>
        </div>
      </div>
    </div>
  );
}

function DetailSection({
  title,
  value,
}: {
  title: string;
  value?: string | null;
}) {
  return (
    <section>
      <SectionLabel>
        {title}
      </SectionLabel>

      <p className="text-[13px] text-muted-foreground leading-relaxed">
        {value || 'No information available.'}
      </p>
    </section>
  );
}