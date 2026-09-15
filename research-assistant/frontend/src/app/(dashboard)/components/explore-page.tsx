'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  Search,
  FileText,
  Network,
  AlertTriangle,
  Lightbulb,
  Telescope,
  TrendingUp,
  SlidersHorizontal,
  Database,
  Sparkles,
  Loader2,
} from 'lucide-react';

import { useExplore } from '@/hooks/use-explore';

import {
  getExploreResults,
} from '@/types/explore';

import {
  SectionLabel,
  Divider,
  MetricLabel,
  ScoreBar,
  TrustTag,
} from '../components/primitives';

import { cn } from './lib/utils';

const topics = [
  'RAG',
  'Agents',
  'Memory',
  'Retrieval',
  'Self-reflection',
  'Tool use',
  'Reasoning',
  'Search',
  'Planning',
  'Multimodal',
  'Interpretability',
  'Test-time compute',
];

const quickExploreItems = [
  {
    label: 'Connections',
    description: 'Explore relationships between retrieved research',
    icon: Network,
    href: '/graph',
    color: 'text-primary-soft',
  },
  {
    label: 'Contradictions',
    description: 'Identify conflicting claims across papers',
    icon: AlertTriangle,
    href: '/explore',
    color: 'text-warning',
  },
  {
    label: 'Frontier',
    description: 'Discover emerging research directions',
    icon: Telescope,
    href: '/frontier',
    color: 'text-primary-soft',
  },
  {
    label: 'Trends',
    description: 'Track research momentum and development',
    icon: TrendingUp,
    href: '/explore',
    color: 'text-success',
  },
];

function getResultId(result: any): string {
  return (
    result?.chunk_id ??
    result?.id ??
    result?.document_id ??
    `${result?.rank ?? Math.random()}`
  );
}

function getResultTitle(result: any): string {
  return (
    result?.document_title ??
    result?.paper_title ??
    result?.title ??
    'Untitled document'
  );
}

function getResultContext(result: any): string {
  return (
    result?.context ??
    result?.content ??
    result?.text ??
    result?.snippet ??
    ''
  );
}

function getResultScore(result: any): number {
  const score = Number(
    result?.score ??
      result?.similarity ??
      result?.relevance_score ??
      result?.distance ??
      0,
  );

  if (!Number.isFinite(score)) {
    return 0;
  }

  if (score <= 1) {
    return Math.round(score * 100);
  }

  return Math.round(Math.min(score, 100));
}

function getResultDocumentId(result: any): string | null {
  return (
    result?.document_id ??
    result?.paper_id ??
    result?.document?.id ??
    result?.paper?.id ??
    null
  );
}

export function ExplorePage() {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');

  const exploreMutation = useExplore();

  const results = useMemo(() => {
    const response = exploreMutation.data;

    if (!response) {
      return [];
    }

    return getExploreResults(response);
  }, [exploreMutation.data]);

  const handleSearch = async () => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      return;
    }

    setSubmittedQuery(trimmedQuery);

    await exploreMutation.mutateAsync({
      query: trimmedQuery,
      adaptive: true,
      top_k: 5,
      retrieval_mode: 'hybrid',
      max_iterations: 3,
      confidence_threshold: 0.75,
      enable_graph: false,
      enable_multi_query: false,
      enable_correction: true,
    });
  };

  const handleTopicSearch = async (topic: string) => {
    setQuery(topic);
    setSubmittedQuery(topic);

    await exploreMutation.mutateAsync({
      query: topic,
      adaptive: true,
      top_k: 5,
      retrieval_mode: 'hybrid',
      max_iterations: 3,
      confidence_threshold: 0.75,
      enable_graph: false,
      enable_multi_query: false,
      enable_correction: true,
    });
  };

  const isSearching = exploreMutation.isPending;

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 md:px-10">
      {/* Header */}
      <div className="mb-8">
        <div className="mb-2 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />

          <span className="font-mono-tech text-[10px] uppercase tracking-widest text-faint">
            Research Intelligence
          </span>
        </div>

        <h1 className="text-xl font-medium tracking-tight text-foreground">
          Explore
        </h1>

        <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
          Search your research knowledge base and discover relevant evidence,
          papers, concepts, and connections.
        </p>
      </div>

      <Divider />

      {/* Explore / Adaptive Retrieval search */}
      <section className="py-8">
        <SectionLabel>Knowledge Retrieval</SectionLabel>

        <div className="mt-4 rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center gap-3">
            <Search className="h-4 w-4 shrink-0 text-faint" />

            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  void handleSearch();
                }
              }}
              placeholder="Ask a research question or search your knowledge base..."
              className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-faint"
            />

            <button
              type="button"
              onClick={() => void handleSearch()}
              disabled={!query.trim() || isSearching}
              className={cn(
                'flex items-center gap-2 rounded-md border px-3 py-2 text-xs transition-colors',
                'border-border bg-background text-foreground',
                'hover:border-strong-border hover:bg-elevated',
                'disabled:cursor-not-allowed disabled:opacity-40',
              )}
            >
              {isSearching ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Search className="h-3.5 w-3.5" />
              )}

              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-border/60 pt-3">
            <div className="flex items-center gap-2 text-[10px] text-faint">
              <Database className="h-3 w-3" />

              <span className="font-mono-tech uppercase tracking-wider">
                Adaptive hybrid retrieval
              </span>
            </div>

            <div className="flex items-center gap-2">
              <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono-tech text-[9px] text-faint">
                ENTER
              </kbd>

              <span className="text-[10px] text-faint">search</span>
            </div>
          </div>
        </div>

        {/* Explore error */}
        {exploreMutation.isError && (
          <div className="mt-3 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />

              <div>
                <p className="text-[12px] font-medium text-foreground">
                  Exploration failed
                </p>

                <p className="mt-1 text-[11px] text-muted-foreground">
                  {exploreMutation.error instanceof Error
                    ? exploreMutation.error.message
                    : 'Unable to explore the research knowledge base at this time.'}
                </p>
              </div>
            </div>
          </div>
        )}
      </section>

      <Divider />

      {/* Search results */}
      {submittedQuery && (
        <>
          <section className="py-8">
            <div className="flex items-center justify-between">
              <div>
                <SectionLabel>Retrieved Evidence</SectionLabel>

                <p className="mt-2 text-[12px] text-muted-foreground">
                  Results for{' '}
                  <span className="text-foreground">
                    &ldquo;{submittedQuery}&rdquo;
                  </span>
                </p>
              </div>

              {!isSearching && (
                <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                  {results.length} result{results.length === 1 ? '' : 's'}
                </span>
              )}
            </div>

            {isSearching ? (
              <div className="mt-5 rounded-lg border border-border bg-surface px-6 py-10">
                <div className="flex flex-col items-center justify-center text-center">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />

                  <p className="mt-3 text-[12px] text-muted-foreground">
                    Searching the research knowledge base...
                  </p>
                </div>
              </div>
            ) : results.length === 0 ? (
              <div className="mt-5 rounded-lg border border-border bg-surface px-6 py-10 text-center">
                <FileText className="mx-auto h-5 w-5 text-faint" />

                <p className="mt-3 text-[12px] text-muted-foreground">
                  No relevant evidence was found.
                </p>

                <p className="mt-1 text-[11px] text-faint">
                  Try a broader research question or another topic.
                </p>
              </div>
            ) : (
              <div className="mt-5 space-y-2">
                {results.map((result: any, index: number) => {
                  const id = getResultId(result);
                  const title = getResultTitle(result);
                  const context = getResultContext(result);
                  const score = getResultScore(result);
                  const documentId = getResultDocumentId(result);

                  return (
                    <div
                      key={`${id}-${index}`}
                      className="group rounded-lg border border-border bg-surface p-4 transition-colors hover:border-strong-border"
                    >
                      <div className="flex items-start gap-4">
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-background">
                          <FileText className="h-3.5 w-3.5 text-primary-soft" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                              <h3 className="truncate text-[13px] font-medium text-foreground">
                                {title}
                              </h3>

                              {result?.document_id && (
                                <span className="mt-1 block font-mono-tech text-[9px] text-faint">
                                  DOCUMENT {result.document_id}
                                </span>
                              )}
                            </div>

                            <div className="shrink-0 text-right">
                              <MetricLabel>Relevance</MetricLabel>

                              <span className="mt-0.5 block font-mono-tech text-[11px] tabular-nums text-secondary-foreground">
                                {score}
                              </span>
                            </div>
                          </div>

                          {context && (
                            <p className="mt-3 line-clamp-4 text-[12px] leading-relaxed text-muted-foreground">
                              {context}
                            </p>
                          )}

                          <div className="mt-4 flex items-center gap-4">
                            <div className="w-32">
                              <ScoreBar value={score} className="mt-1" />
                            </div>

                            <TrustTag category="evidence" />

                            {documentId ? (
                              <Link
                                href={`/papers/${documentId}`}
                                className="ml-auto flex items-center gap-1.5 text-[11px] text-faint transition-colors hover:text-primary"
                              >
                                Open source
                                <ArrowRight className="h-3 w-3" />
                              </Link>
                            ) : (
                              <span className="ml-auto font-mono-tech text-[10px] text-faint">
                                RESULT {index + 1}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <Divider />
        </>
      )}

      {/* Topics */}
      <section className="py-8">
        <SectionLabel>Research Topics</SectionLabel>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {topics.map((topic) => (
            <button
              key={topic}
              type="button"
              onClick={() => void handleTopicSearch(topic)}
              className="rounded-full border border-border px-3 py-1 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:bg-surface hover:text-foreground"
            >
              {topic}
            </button>
          ))}
        </div>
      </section>

      <Divider />

      {/* Research workflows */}
      <section className="py-8">
        <SectionLabel>Research Workflows</SectionLabel>

        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <Link
            href="/papers"
            className="group rounded-lg border border-border bg-surface p-4 transition-colors hover:border-strong-border"
          >
            <FileText className="mb-3 h-4 w-4 text-primary-soft" />

            <h3 className="text-[13px] font-medium text-foreground">
              Search Papers
            </h3>

            <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
              Browse, filter, and inspect your research paper collection.
            </p>

            <div className="mt-4 flex items-center gap-1 text-[10px] text-faint transition-colors group-hover:text-primary">
              Open papers
              <ArrowRight className="h-3 w-3" />
            </div>
          </Link>

          <Link
            href="/reports"
            className="group rounded-lg border border-border bg-surface p-4 transition-colors hover:border-strong-border"
          >
            <Lightbulb className="mb-3 h-4 w-4 text-warning" />

            <h3 className="text-[13px] font-medium text-foreground">
              Synthesize Research
            </h3>

            <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
              Turn retrieved evidence into structured research reports.
            </p>

            <div className="mt-4 flex items-center gap-1 text-[10px] text-faint transition-colors group-hover:text-primary">
              View reports
              <ArrowRight className="h-3 w-3" />
            </div>
          </Link>

          <Link
            href="/graph"
            className="group rounded-lg border border-border bg-surface p-4 transition-colors hover:border-strong-border"
          >
            <Network className="mb-3 h-4 w-4 text-primary-soft" />

            <h3 className="text-[13px] font-medium text-foreground">
              Research Graph
            </h3>

            <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
              Explore relationships between papers, concepts, and citations.
            </p>

            <div className="mt-4 flex items-center gap-1 text-[10px] text-faint transition-colors group-hover:text-primary">
              Explore graph
              <ArrowRight className="h-3 w-3" />
            </div>
          </Link>
        </div>
      </section>

      <Divider />

      {/* Explore by */}
      <section className="py-8">
        <div className="flex items-center justify-between">
          <SectionLabel>Explore By</SectionLabel>

          <SlidersHorizontal className="h-3.5 w-3.5 text-faint" />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          {quickExploreItems.map((item) => {
            const Icon = item.icon;

            return (
              <Link
                key={item.label}
                href={item.href}
                className="group rounded-lg border border-border bg-surface p-4 transition-colors hover:border-strong-border"
              >
                <Icon className={cn('mb-3 h-4 w-4', item.color)} />

                <p className="text-[13px] text-foreground transition-colors group-hover:text-primary-soft">
                  {item.label}
                </p>

                <p className="mt-1 text-[10px] leading-relaxed text-faint">
                  {item.description}
                </p>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}