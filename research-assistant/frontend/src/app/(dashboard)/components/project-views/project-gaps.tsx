'use client';

import { useState } from 'react';

import {
  SectionLabel,
  MetricLabel,
  Divider,
} from '../../components/primitives';

import { cn } from '../lib/utils';
import { useFrontierGaps } from '@/frontier/hooks/use-frontier-gaps';


export function ProjectGaps({
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
  } = useFrontierGaps(projectId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="h-6 w-40 bg-surface animate-pulse rounded" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-24 bg-surface animate-pulse rounded"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load research gaps.
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

  const gaps = data?.items ?? [];

  if (!gaps.length) {
    return (
      <div className="mx-auto max-w-5xl py-16 text-center">
        <p className="text-sm text-muted-foreground">
          No research gaps identified yet.
        </p>
      </div>
    );
  }

  const gap =
    gaps[Math.min(active, gaps.length - 1)];

  return (
    <div className="mx-auto max-w-5xl">
      <SectionLabel>
        Research Gaps
      </SectionLabel>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <div className="space-y-1">
          {gaps.map((item, index) => (
            <button
              key={item.id}
              onClick={() =>
                setActive(index)
              }
              className={cn(
                'w-full text-left rounded-md border px-4 py-3 transition-colors',
                active === index
                  ? 'border-warning/40 bg-warning/5'
                  : 'border-border bg-surface hover:border-strong-border',
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono-tech text-[10px] uppercase text-warning">
                  GAP
                </span>

                <span className="font-mono-tech text-[10px] text-faint">
                  {item.id}
                </span>
              </div>

              <p className="text-[13px] text-foreground leading-relaxed">
                {item.title}
              </p>
            </button>
          ))}
        </div>

        <div className="rounded-lg border border-border bg-surface p-6">
          <div className="flex items-start justify-between gap-4 mb-6">
            <div>
              <span className="font-mono-tech text-[10px] uppercase tracking-wider text-warning">
                Research Gap
              </span>

              <h3 className="text-[18px] font-medium text-foreground mt-1">
                {gap.title}
              </h3>
            </div>

            <div className="text-right">
              <MetricLabel>
                Confidence
              </MetricLabel>

              <p className="font-mono-tech text-lg text-warning tabular-nums">
                {gap.confidence}
              </p>
            </div>
          </div>

          <section className="mb-6">
            <SectionLabel>
              Description
            </SectionLabel>

            <p className="text-[14px] text-secondary-foreground leading-relaxed">
              {gap.description}
            </p>
          </section>

          <Divider className="mb-6" />

          <section className="mb-6">
            <SectionLabel>
              Why This Is a Gap
            </SectionLabel>

            <div className="space-y-2">
              {gap.reasons?.map(
                (reason, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3"
                  >
                    <span className="font-mono-tech text-[11px] text-faint">
                      {String(index + 1).padStart(
                        2,
                        '0',
                      )}
                    </span>

                    <span className="text-[13px] text-muted-foreground">
                      {reason}
                    </span>
                  </div>
                ),
              )}
            </div>
          </section>

          <Divider className="mb-6" />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <MetricLabel>
                Relevant papers
              </MetricLabel>

              <p className="font-mono-tech text-lg text-secondary-foreground tabular-nums">
                {gap.relevantPapers ?? 0}
              </p>
            </div>

            <div>
              <MetricLabel>
                Opportunity
              </MetricLabel>

              <p className="font-mono-tech text-lg text-primary-soft tabular-nums">
                {gap.opportunity ?? '—'}
              </p>
            </div>
          </div>

          {gap.suggestedDirection && (
            <div className="mt-6 pt-5 border-t border-border">
              <SectionLabel>
                Suggested Direction
              </SectionLabel>

              <p className="text-[13px] text-secondary-foreground leading-relaxed">
                {gap.suggestedDirection}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}