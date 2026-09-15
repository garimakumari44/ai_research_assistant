'use client';

import { useState } from 'react';
import {
  SectionLabel,
  TrustTag,
  Divider,
} from '../../components/primitives';
import { cn } from '../lib/utils';
import type { TrustCategory } from '../lib/types';
import { useProjectEvidence } from '@/retrieval/hooks/use-project-evidence';

const categoryFilters: (
  | TrustCategory
  | 'all'
)[] = [
  'all',
  'evidence',
  'inference',
  'forecast',
  'hypothesis',
];

export function ProjectEvidence({
  projectId,
}: {
  projectId: string;
}) {
  const [filter, setFilter] =
    useState<TrustCategory | 'all'>('all');

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useProjectEvidence(projectId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="h-5 w-48 bg-surface animate-pulse rounded" />

        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-28 bg-surface animate-pulse rounded"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-4xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load evidence.
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

  const allEvidence = data?.evidence ?? [];

  const filtered =
    filter === 'all'
      ? allEvidence
      : allEvidence.filter(
          (item) =>
            item.trustCategory === filter,
        );

  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <SectionLabel className="mb-0">
          Evidence · {filtered.length} units
        </SectionLabel>

        <div className="flex items-center gap-1 flex-wrap">
          {categoryFilters.map((category) => (
            <button
              key={category}
              onClick={() =>
                setFilter(category)
              }
              className={cn(
                'rounded-sm border px-2 py-1 font-mono-tech text-[10px] uppercase tracking-wider transition-colors',
                filter === category
                  ? 'border-primary text-primary-soft bg-primary/5'
                  : 'border-border text-faint hover:text-muted-foreground',
              )}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <div>
        {filtered.map((item, index) => (
          <div key={item.id}>
            {index > 0 && (
              <Divider className="my-0" />
            )}

            <div className="py-5 group">
              <div className="flex items-center gap-3 mb-3">
                <TrustTag
                  category={
                    item.trustCategory
                  }
                />

                <span className="font-mono-tech text-[11px] text-faint">
                  {item.id}
                </span>

                <span className="font-mono-tech text-[10px] text-faint uppercase tracking-wider">
                  {item.category}
                </span>
              </div>

              <blockquote className="text-[14px] text-secondary-foreground leading-relaxed border-l-2 border-border pl-4 mb-3">
                {item.quote}
              </blockquote>

              <div className="flex items-center gap-4 flex-wrap">
                <span className="text-[13px] text-primary-soft">
                  {item.paperTitle}
                </span>

                {(item.section ||
                  item.page) && (
                  <span className="font-mono-tech text-[11px] text-faint">
                    {item.section}
                    {item.page
                      ? ` · p.${item.page}`
                      : ''}
                  </span>
                )}

                {typeof item.relevance ===
                  'number' && (
                  <span className="font-mono-tech text-[11px] text-faint">
                    Relevance{' '}
                    <span className="text-secondary-foreground tabular-nums">
                      {item.relevance.toFixed(
                        2,
                      )}
                    </span>
                  </span>
                )}

                <button className="ml-auto text-[11px] text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100">
                  Open source →
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-[14px] text-muted-foreground">
            No evidence in this category.
          </p>
        </div>
      )}
    </div>
  );
}