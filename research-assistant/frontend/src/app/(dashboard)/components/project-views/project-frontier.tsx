'use client';

import { useState } from 'react';
import {
  SectionLabel,
  Divider,
  MetricLabel,
  ScoreBar,
  ConfidenceMeter,
  TrustTag,
} from '../../components/primitives';
import { cn } from '../lib/utils';
import { useFrontier } from '@/frontier/hooks/use-frontier';

interface ProjectFrontierProps {
  projectId: string;
}

export function ProjectFrontier({
  projectId,
}: ProjectFrontierProps) {
  const [active, setActive] = useState(0);

  const {
    data,
    isLoading,
    isError,
  } = useFrontier(projectId);

  const frontier = data?.items ?? [];
  const current = frontier[active];

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl">
        <SectionLabel>Research Frontier</SectionLabel>

        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-[13px] text-muted-foreground">
            Analyzing research frontier…
          </p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl">
        <SectionLabel>Research Frontier</SectionLabel>

        <div className="rounded-lg border border-danger/30 bg-danger/5 p-6">
          <p className="text-[13px] text-danger">
            Unable to load frontier analysis.
          </p>
        </div>
      </div>
    );
  }

  if (!current) {
    return (
      <div className="mx-auto max-w-5xl">
        <SectionLabel>Research Frontier</SectionLabel>

        <div className="rounded-lg border border-border bg-surface p-8 text-center">
          <p className="text-[13px] text-muted-foreground">
            No frontier analysis is available for this project.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <SectionLabel>Research Frontier</SectionLabel>

      <div className="rounded-lg border border-border bg-surface p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
            Past
          </span>

          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-primary-soft">
            Current
          </span>

          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-warning">
            Future
          </span>
        </div>

        <div className="relative h-px bg-border mb-6">
          <div className="absolute left-0 top-0 h-px w-1/3 bg-muted-foreground" />
          <div className="absolute left-1/3 top-0 h-px w-1/3 bg-primary" />
          <div className="absolute left-2/3 top-0 h-px w-1/3 border-t border-dashed border-warning" />
        </div>

        <div className="space-y-2">
          {frontier.map((item) => {
            const level =
              item.horizon ??
              (item.forecast === 'future'
                ? 'future'
                : 'current');

            return (
              <div
                key={item.id ?? item.name}
                className="flex items-center gap-3"
              >
                <div
                  className={cn(
                    'h-1.5 w-1.5 rounded-full',
                    level === 'past'
                      ? 'bg-faint'
                      : level === 'future'
                        ? 'bg-warning'
                        : 'bg-primary',
                  )}
                />

                <span
                  className={cn(
                    'text-[12px]',
                    level === 'past'
                      ? 'text-faint'
                      : level === 'future'
                        ? 'text-warning'
                        : 'text-foreground',
                  )}
                >
                  {item.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col gap-1 mb-6">
        {frontier.map((item, index) => (
          <button
            key={item.id ?? item.name}
            onClick={() => setActive(index)}
            className={cn(
              'text-left rounded-md border px-4 py-3 transition-colors',
              active === index
                ? 'border-primary/40 bg-primary/5'
                : 'border-border bg-surface hover:border-strong-border',
            )}
          >
            <div className="flex items-center justify-between">
              <span
                className={cn(
                  'text-[13px] font-medium',
                  active === index
                    ? 'text-foreground'
                    : 'text-muted-foreground',
                )}
              >
                {item.name}
              </span>

              <span className="font-mono-tech text-[11px] text-faint">
                Momentum{' '}
                <span className="text-secondary-foreground tabular-nums">
                  {item.momentum}
                </span>
              </span>
            </div>
          </button>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-[16px] font-medium text-foreground">
            {current.name}
          </h3>

          <div className="flex items-center gap-3">
            <TrustTag category="forecast" />

            <ConfidenceMeter
              value={current.confidence}
              label="Confidence"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-6">
          <div>
            <MetricLabel>Observed momentum</MetricLabel>

            <ScoreBar
              value={current.momentum}
              className="mt-2"
            />

            <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-1 block">
              {current.momentum}
            </span>
          </div>

          <div>
            <MetricLabel>Cross-topic convergence</MetricLabel>

            <ScoreBar
              value={current.convergence}
              color="bg-primary-soft"
              className="mt-2"
            />

            <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-1 block">
              {current.convergence}
            </span>
          </div>

          <div>
            <MetricLabel>Novelty</MetricLabel>

            <ScoreBar
              value={current.novelty}
              color="bg-success"
              className="mt-2"
            />

            <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-1 block">
              {current.novelty}
            </span>
          </div>
        </div>

        <Divider className="mb-6" />

        <section className="mb-6">
          <SectionLabel>Why?</SectionLabel>

          <div className="space-y-1">
            {current.reasons?.map((reason: string, index: number) => (
              <div
                key={index}
                className="flex items-center gap-3 py-2 border-b border-border/50"
              >
                <span className="font-mono-tech text-[11px] text-faint tabular-nums">
                  {String(index + 1).padStart(2, '0')}
                </span>

                <span className="text-[13px] text-secondary-foreground">
                  {reason}
                </span>
              </div>
            ))}
          </div>
        </section>

        <Divider className="mb-6" />

        <div className="grid grid-cols-3 gap-4">
          <div>
            <MetricLabel>Supporting evidence</MetricLabel>

            <p className="font-mono-tech text-lg text-success tabular-nums mt-1">
              {current.supportingEvidence}
            </p>
          </div>

          <div>
            <MetricLabel>Counter-signals</MetricLabel>

            <p className="font-mono-tech text-lg text-warning tabular-nums mt-1">
              {current.counterSignals}
            </p>
          </div>

          <div>
            <MetricLabel>Relevant papers</MetricLabel>

            <p className="font-mono-tech text-lg text-secondary-foreground tabular-nums mt-1">
              {current.relevantPapers}
            </p>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-[12px] text-faint italic">
            Forecast:{' '}
            <span className="text-warning capitalize">
              {current.forecast}
            </span>{' '}
            · This is a model-generated projection. Treat as a directional
            signal, not a certainty.
          </p>
        </div>
      </div>
    </div>
  );
}