'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Search,
  FileText,
} from 'lucide-react';

import { MetricLabel } from '../../components/primitives';
import { cn } from '../lib/utils';
import { useProjectPapers } from '@/papers/hooks/use-project-papers';


const filters = [
  'Year',
  'Topic',
  'Method',
  'Venue',
  'Author',
  'Dataset',
];

export function ProjectPapers({
  projectId,
}: {
  projectId: string;
}) {
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] =
    useState<string | null>(null);

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useProjectPapers(projectId, {
    search: query || undefined,
  });

  const papers = data?.items ?? [];

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl">
        <div className="h-10 rounded-md bg-surface animate-pulse mb-6" />
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-md bg-surface animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load project papers.
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
      <div className="mb-6">
        <div className="flex items-center gap-2.5 rounded-md border border-border bg-surface px-3.5 py-2.5">
          <Search className="h-3.5 w-3.5 text-faint" />

          <input
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="Search papers, methods, authors, datasets..."
            className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-faint outline-none"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {filters.map((filter) => (
          <button
            key={filter}
            onClick={() =>
              setActiveFilter(
                activeFilter === filter
                  ? null
                  : filter,
              )
            }
            className={cn(
              'rounded-full border px-3 py-1 text-[12px] transition-colors',
              activeFilter === filter
                ? 'border-primary bg-primary/10 text-primary-soft'
                : 'border-border text-muted-foreground hover:border-strong-border hover:text-foreground',
            )}
          >
            {filter}
          </button>
        ))}

        <div className="ml-auto">
          <MetricLabel>
            {data?.total ?? papers.length} results
          </MetricLabel>
        </div>
      </div>

      <div>
        {papers.map((paper, index) => (
          <div
            key={paper.id}
            className="group flex items-start gap-4 py-4 border-b border-border/50 hover:bg-surface/50 -mx-2 px-2 rounded transition-colors"
          >
            <span className="font-mono-tech text-[11px] text-faint tabular-nums mt-0.5 w-6 shrink-0">
              {String(index + 1).padStart(2, '0')}
            </span>

            <div className="flex-1 min-w-0">
              <Link
                href={`/papers/${paper.id}`}
                className="text-[14px] font-medium text-foreground hover:text-primary-soft transition-colors"
              >
                {paper.title}
              </Link>

              <p className="text-[12px] text-faint mt-0.5 mb-1.5">
                {paper.authors?.join(', ')}
                {' · '}
                {paper.venue}
                {' · '}
                {paper.year}
              </p>

              {paper.abstract && (
                <p className="text-[12px] text-muted-foreground leading-relaxed mb-2 line-clamp-2">
                  {paper.abstract}
                </p>
              )}

              <div className="flex items-center gap-1.5 flex-wrap">
                {paper.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="font-mono-tech text-[10px] text-muted-foreground border border-border rounded px-1.5 py-0.5"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="shrink-0 text-right">
              <p className="font-mono-tech text-[10px] text-faint uppercase tracking-wider">
                Citations
              </p>

              <p className="font-mono-tech text-sm text-secondary-foreground tabular-nums">
                {paper.citations ?? 0}
              </p>
            </div>
          </div>
        ))}
      </div>

      {papers.length === 0 && (
        <div className="py-16 text-center">
          <FileText className="h-6 w-6 text-faint mx-auto mb-3" />

          <p className="text-[14px] text-muted-foreground mb-1">
            No papers match your search.
          </p>

          <p className="text-[12px] text-faint">
            Try a different query or clear filters.
          </p>
        </div>
      )}
    </div>
  );
}