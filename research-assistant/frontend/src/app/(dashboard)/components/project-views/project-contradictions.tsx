'use client';

import { useState } from 'react';

import {
  SectionLabel,
  Divider,
  MetricLabel,
} from '../../components/primitives';

import { cn } from '../lib/utils';
import { useProjectContradictions } from '@/retrieval/hooks/use-project-contradictions';


export function ProjectContradictions({
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
  } = useProjectContradictions(projectId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="h-6 w-56 bg-surface animate-pulse rounded" />
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
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load contradiction analysis.
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

  const contradictions =
    data?.items ?? [];

  if (!contradictions.length) {
    return (
      <div className="mx-auto max-w-5xl py-16 text-center">
        <p className="text-sm text-muted-foreground">
          No contradictions have been identified.
        </p>
      </div>
    );
  }

  const claim =
    contradictions[
      Math.min(
        active,
        contradictions.length - 1,
      )
    ];

  const supporting =
    claim.papers?.filter(
      (paper) => paper.stance === 'support',
    ) ?? [];

  const contradicting =
    claim.papers?.filter(
      (paper) =>
        paper.stance === 'contradict',
    ) ?? [];

  const qualifying =
    claim.papers?.filter(
      (paper) =>
        paper.stance === 'qualify',
    ) ?? [];

  return (
    <div className="mx-auto max-w-5xl">
      <SectionLabel>
        Contradiction Explorer
      </SectionLabel>

      <div className="flex flex-col gap-1 mb-8">
        {contradictions.map(
          (item, index) => (
            <button
              key={item.id}
              onClick={() =>
                setActive(index)
              }
              className={cn(
                'text-left rounded-md border px-4 py-3 transition-colors',
                active === index
                  ? 'border-warning/40 bg-warning/5'
                  : 'border-border bg-surface hover:border-strong-border',
              )}
            >
              <div className="flex items-center gap-3">
                <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                  Claim
                </span>

                <p className="text-[13px] text-foreground">
                  {item.claim}
                </p>
              </div>
            </button>
          ),
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 mb-8">
        <CountCard
          label="Supporting"
          value={
            claim.supporting ??
            supporting.length
          }
          color="success"
        />

        <CountCard
          label="Contradicting"
          value={
            claim.contradicting ??
            contradicting.length
          }
          color="danger"
        />

        <CountCard
          label="Qualifying"
          value={
            claim.qualifying ??
            qualifying.length
          }
          color="warning"
        />
      </div>

      <Divider className="mb-8" />

      <section className="mb-8">
        <SectionLabel>
          Why?
        </SectionLabel>

        <div className="space-y-1">
          {claim.reasons?.map(
            (reason, index) => (
              <div
                key={index}
                className="flex items-start gap-3 py-2.5 border-b border-border/50"
              >
                <span className="font-mono-tech text-[11px] text-faint tabular-nums">
                  {String(index + 1).padStart(
                    2,
                    '0',
                  )}
                </span>

                <span className="text-[13px] text-secondary-foreground">
                  {reason}
                </span>
              </div>
            ),
          )}
        </div>
      </section>

      <Divider className="mb-8" />

      <section>
        <SectionLabel>
          Evidence
        </SectionLabel>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <EvidenceColumn
            title="Supporting"
            papers={supporting}
            tone="success"
          />

          <EvidenceColumn
            title="Contradicting"
            papers={contradicting}
            tone="danger"
          />
        </div>

        {qualifying.length > 0 && (
          <div className="mt-3">
            <EvidenceColumn
              title="Qualifying"
              papers={qualifying}
              tone="warning"
            />
          </div>
        )}
      </section>
    </div>
  );
}

function CountCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'success' | 'danger' | 'warning';
}) {
  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        color === 'success' &&
          'border-success/30 bg-success/5',
        color === 'danger' &&
          'border-danger/30 bg-danger/5',
        color === 'warning' &&
          'border-warning/30 bg-warning/5',
      )}
    >
      <MetricLabel>
        {label}
      </MetricLabel>

      <p
        className={cn(
          'font-mono-tech text-2xl tabular-nums mt-1',
          color === 'success' &&
            'text-success',
          color === 'danger' &&
            'text-danger',
          color === 'warning' &&
            'text-warning',
        )}
      >
        {value}
      </p>

      <p className="text-[11px] text-faint mt-1">
        papers
      </p>
    </div>
  );
}

function EvidenceColumn({
  title,
  papers,
  tone,
}: {
  title: string;
  papers: Array<{
    title: string;
    note?: string;
  }>;
  tone: 'success' | 'danger' | 'warning';
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center gap-2 mb-3">
        <div
          className={cn(
            'h-2 w-2 rounded-full',
            tone === 'success' &&
              'bg-success',
            tone === 'danger' &&
              'bg-danger',
            tone === 'warning' &&
              'bg-warning',
          )}
        />

        <span
          className={cn(
            'font-mono-tech text-[11px] uppercase tracking-wider',
            tone === 'success' &&
              'text-success',
            tone === 'danger' &&
              'text-danger',
            tone === 'warning' &&
              'text-warning',
          )}
        >
          {title}
        </span>
      </div>

      <div className="space-y-3">
        {papers.map((paper, index) => (
          <div
            key={`${paper.title}-${index}`}
            className="border-b border-border/50 pb-3 last:border-0"
          >
            <p className="text-[13px] text-foreground mb-1">
              {paper.title}
            </p>

            {paper.note && (
              <p className="text-[12px] text-muted-foreground">
                {paper.note}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}