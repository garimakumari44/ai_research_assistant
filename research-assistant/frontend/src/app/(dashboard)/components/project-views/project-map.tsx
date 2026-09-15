'use client';

import { useMemo, useState } from 'react';
import { SectionLabel, MetricLabel } from '../../components/primitives';
import { cn } from '../lib/utils';
import { useGraph } from '@/graph/hooks/use-graph';

import type { GraphNode } from '@/graph/types';

const nodeTypeFill: Record<string, string> = {
  paper: '#3B82F6',
  topic: '#22C55E',
  method: '#F59E0B',
  author: '#60A5FA',
  dataset: '#EF4444',
};

const filterTypes = [
  'all',
  'paper',
  'topic',
  'method',
  'author',
  'dataset',
] as const;

type FilterType = (typeof filterTypes)[number];

export function ProjectMap({ projectId: _projectId }: { projectId: string }) {
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');

  const { data, isLoading, isError, refetch } = useGraph({
    depth: 2,
  });

  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];

  const visibleNodes = useMemo(() => {
    if (activeFilter === 'all') {
      return nodes;
    }

    return nodes.filter((node) => node.type === activeFilter);
  }, [nodes, activeFilter]);

  const visibleIds = useMemo(
    () => new Set(visibleNodes.map((node) => node.id)),
    [visibleNodes],
  );

  const visibleEdges = useMemo(
    () =>
      edges.filter(
        (edge) =>
          visibleIds.has(edge.source) &&
          visibleIds.has(edge.target),
      ),
    [edges, visibleIds],
  );

  if (isLoading) {
    return <ProjectMapLoading />;
  }

  if (isError) {
    return (
      <ProjectViewError
        message="Unable to load the research graph."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <SectionLabel className="mb-0">
          Literature Map
        </SectionLabel>

        <div className="flex items-center gap-1">
          {filterTypes.map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={cn(
                'rounded-sm border px-2 py-1 font-mono-tech text-[10px] uppercase tracking-wider transition-colors',
                activeFilter === filter
                  ? 'border-primary text-primary-soft bg-primary/5'
                  : 'border-border text-faint hover:text-muted-foreground',
              )}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        <div
          className="relative rounded-lg border border-border bg-surface overflow-hidden grid-bg"
          style={{ minHeight: '500px' }}
        >
          <svg
            width="100%"
            height="500"
            viewBox="0 0 800 500"
            className="block"
          >
            {visibleEdges.map((edge) => {
              const from = nodes.find(
                (node) => node.id === edge.source,
              );
              const to = nodes.find(
                (node) => node.id === edge.target,
              );

              if (!from || !to) {
                return null;
              }

              const fromX = from.x ?? from.position?.x ?? 0;
              const fromY = from.y ?? from.position?.y ?? 0;
              const toX = to.x ?? to.position?.x ?? 0;
              const toY = to.y ?? to.position?.y ?? 0;
              const strength = edge.strength ?? 1;

              return (
                <line
                  key={edge.id}
                  x1={fromX}
                  y1={fromY}
                  x2={toX}
                  y2={toY}
                  stroke="hsl(var(--strong-border))"
                  strokeWidth={Math.max(1, strength * 1.5)}
                  opacity={0.5}
                />
              );
            })}

            {visibleNodes.map((node) => {
              const fill =
                nodeTypeFill[node.type] ?? '#3B82F6';

              const x = node.x ?? node.position?.x ?? 0;
              const y = node.y ?? node.position?.y ?? 0;
              const size = node.size ?? 20;

              return (
                <g
                  key={node.id}
                  onClick={() => setSelected(node)}
                  className="cursor-pointer"
                >
                  <circle
                    cx={x}
                    cy={y}
                    r={size / 2}
                    fill={fill}
                    opacity={
                      selected && selected.id !== node.id
                        ? 0.3
                        : 0.8
                    }
                  />

                  <circle
                    cx={x}
                    cy={y}
                    r={size / 2}
                    fill="none"
                    stroke={fill}
                    strokeWidth={
                      selected?.id === node.id ? 2 : 0
                    }
                  />

                  <text
                    x={x}
                    y={y + size / 2 + 14}
                    textAnchor="middle"
                    className="fill-muted-foreground text-[10px] font-mono-tech pointer-events-none select-none"
                  >
                    {node.label.length > 20
                      ? `${node.label.slice(0, 18)}…`
                      : node.label}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="absolute bottom-3 left-3 flex items-center gap-3 rounded-md border border-border bg-elevated/90 px-3 py-2 backdrop-blur">
            {(
              [
                'paper',
                'topic',
                'method',
                'author',
                'dataset',
              ] as string[]
            ).map((type) => (
              <div
                key={type}
                className="flex items-center gap-1.5"
              >
                <div
                  className="h-2 w-2 rounded-full"
                  style={{
                    background: nodeTypeFill[type],
                  }}
                />

                <span className="font-mono-tech text-[10px] text-faint uppercase">
                  {type}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4 h-fit">
          {selected ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="h-2.5 w-2.5 rounded-full"
                  style={{
                    background:
                      nodeTypeFill[selected.type] ??
                      '#3B82F6',
                  }}
                />

                <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                  {selected.type}
                </span>
              </div>

              <h3 className="text-[14px] font-medium text-foreground mb-4">
                {selected.label}
              </h3>

              <div className="space-y-3">
                <div>
                  <MetricLabel>
                    Connections
                  </MetricLabel>

                  <p className="font-mono-tech text-sm text-secondary-foreground tabular-nums mt-0.5">
                    {selected.connections ?? 0}
                  </p>
                </div>

                <div>
                  <MetricLabel>
                    Related edges
                  </MetricLabel>

                  <p className="font-mono-tech text-sm text-secondary-foreground tabular-nums mt-0.5">
                    {
                      visibleEdges.filter(
                        (edge) =>
                          edge.source === selected.id ||
                          edge.target === selected.id,
                      ).length
                    }
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-border">
                <button className="text-[12px] text-primary-soft hover:underline">
                  Focus node
                </button>

                <button className="text-[12px] text-muted-foreground hover:text-foreground block mt-1.5">
                  Expand cluster
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-[13px] text-muted-foreground mb-1">
                Select a node
              </p>

              <p className="text-[11px] text-faint">
                Click any node to inspect its connections
                and context.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProjectMapLoading() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="h-5 w-32 bg-surface rounded animate-pulse mb-6" />
      <div className="h-[500px] rounded-lg border border-border bg-surface animate-pulse" />
    </div>
  );
}

function ProjectViewError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="mx-auto max-w-6xl rounded-lg border border-danger/30 bg-danger/5 p-8 text-center">
      <p className="text-[13px] text-muted-foreground mb-3">
        {message}
      </p>

      <button
        onClick={onRetry}
        className="rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground hover:text-foreground"
      >
        Retry
      </button>
    </div>
  );
}