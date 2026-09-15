
'use client';

import { useMemo, useState } from 'react';
import { ReactFlowProvider } from '@xyflow/react';

import { useGraph } from '@/graph/hooks/use-graph';
import type {
  GraphNode,
  GraphNodeType,
  GraphEdgeType,
} from '@/graph/types';

import { GraphCanvas } from './graph/graph-canvas';
import { GraphControls } from './graph/graph-controls';
import { GraphDetails } from './graph/graph-details';
import {
  GraphFilters,
  type GraphFiltersState,
} from './graph/graph-filters';
import { GraphLegend } from './graph/graph-legend';
import { GraphSearch } from './graph/graph-search';

export function GraphPage() {
  return (
    <ReactFlowProvider>
      <GraphPageContent />
    </ReactFlowProvider>
  );
}

function GraphPageContent() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    null,
  );

  const [nodeType, setNodeType] = useState<GraphNodeType | 'all'>(
    'all',
  );

  const [edgeType, setEdgeType] = useState<GraphEdgeType | 'all'>(
    'all',
  );

  const [search, setSearch] = useState('');

  const [depth, setDepth] = useState(2);

  const [filters, setFilters] = useState<GraphFiltersState>({
    nodeTypes: [],
    edgeTypes: [],
    minRelevance: 0,
  });

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useGraph({
    depth,
    node_type: nodeType === 'all' ? undefined : nodeType,
    edge_type: edgeType === 'all' ? undefined : edgeType,
    search: search || undefined,
  });

  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];

  const availableNodeTypes = useMemo(() => {
    return Array.from(
      new Set(
        nodes
          .map((node) => node.type)
          .filter(Boolean),
      ),
    );
  }, [nodes]);

  const availableEdgeTypes = useMemo(() => {
    return Array.from(
      new Set(
        edges
          .map((edge) => edge.type)
          .filter(Boolean),
      ),
    );
  }, [edges]);

  const visibleNodes = useMemo(() => {
    let result = nodes;

    if (nodeType !== 'all') {
      result = result.filter(
        (node) => node.type === nodeType,
      );
    }

    if (filters.nodeTypes.length > 0) {
      result = result.filter((node) =>
        filters.nodeTypes.includes(node.type),
      );
    }

    if ((filters.minRelevance ?? 0) > 0) {
      result = result.filter((node) => {
        const relevanceValue = (
          node as GraphNode & {
            relevance?: number;
          }
        ).relevance;

        const relevance =
          typeof relevanceValue === 'number'
            ? relevanceValue
            : 1;

        return relevance >= (filters.minRelevance ?? 0);
      });
    }

    return result;
  }, [
    nodes,
    nodeType,
    filters.nodeTypes,
    filters.minRelevance,
  ]);

  const visibleNodeIds = useMemo(
    () =>
      new Set(
        visibleNodes.map((node) => node.id),
      ),
    [visibleNodes],
  );

  const visibleEdges = useMemo(() => {
    return edges.filter((edge) => {
      const nodesVisible =
        visibleNodeIds.has(edge.source) &&
        visibleNodeIds.has(edge.target);

      if (!nodesVisible) {
        return false;
      }

      if (
        edgeType !== 'all' &&
        edge.type !== edgeType
      ) {
        return false;
      }

      if (
        filters.edgeTypes.length > 0 &&
        !filters.edgeTypes.includes(edge.type)
      ) {
        return false;
      }

      return true;
    });
  }, [
    edges,
    visibleNodeIds,
    edgeType,
    filters.edgeTypes,
  ]);

  const selectedNode = useMemo<GraphNode | null>(() => {
    if (!selectedNodeId) {
      return null;
    }

    return (
      nodes.find(
        (node) => node.id === selectedNodeId,
      ) ?? null
    );
  }, [nodes, selectedNodeId]);

  const handleSelectNode = (node: GraphNode | null) => {
    setSelectedNodeId(node?.id ?? null);
  };

  const handleClearSelection = () => {
    setSelectedNodeId(null);
  };

  const handleFiltersChange = (
    nextFilters: GraphFiltersState,
  ) => {
    setFilters(nextFilters);

    if (nextFilters.nodeTypes.length === 1) {
      setNodeType(
        nextFilters.nodeTypes[0] as GraphNodeType,
      );
    } else {
      setNodeType('all');
    }

    if (nextFilters.edgeTypes.length === 1) {
      setEdgeType(
        nextFilters.edgeTypes[0] as GraphEdgeType,
      );
    } else {
      setEdgeType('all');
    }
  };

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-8 md:px-10">
      <div className="mb-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-xl font-medium tracking-tight text-foreground">
              Research Graph
            </h1>

            <p className="mt-2 text-[13px] text-muted-foreground">
              Explore relationships between papers, authors,
              topics, methods, datasets, and citations.
            </p>
          </div>

          <GraphSearch
            value={search}
            onChange={setSearch}
            onClear={() => setSearch('')}
          />
        </div>
      </div>

      <GraphFilters
        filters={filters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onChange={handleFiltersChange}
      />

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
        <div className="relative min-h-[650px] overflow-hidden rounded-lg border border-border bg-surface">
          {isLoading && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-surface/80 backdrop-blur-sm">
              <div className="text-center">
                <div className="mx-auto mb-3 h-5 w-5 animate-spin rounded-full border-2 border-border border-t-primary" />

                <p className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                  Loading research graph
                </p>
              </div>
            </div>
          )}

          {isError && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-surface">
              <div className="max-w-sm px-6 text-center">
                <p className="text-sm font-medium text-foreground">
                  Unable to load graph
                </p>

                <p className="mt-2 text-xs text-muted-foreground">
                  {error instanceof Error
                    ? error.message
                    : 'The graph service returned an error.'}
                </p>

                <button
                  type="button"
                  onClick={() => refetch()}
                  className="mt-4 rounded-sm border border-border px-3 py-1.5 font-mono-tech text-[10px] uppercase tracking-wider text-primary hover:border-primary"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {!isLoading &&
            !isError &&
            visibleNodes.length === 0 && (
              <div className="absolute inset-0 z-10 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">
                    No graph data found
                  </p>

                  <p className="mt-1 text-[11px] text-faint">
                    Try changing the filters or search query.
                  </p>
                </div>
              </div>
            )}

          <GraphCanvas
            nodes={visibleNodes}
            edges={visibleEdges}
            selectedNodeId={selectedNodeId}
            onNodeSelect={handleSelectNode}
          />

          <GraphLegend />

          <GraphControls
            depth={depth}
            onDepthChange={setDepth}
          />
        </div>

        <GraphDetails
          node={selectedNode}
          onClose={handleClearSelection}
        />
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-5 font-mono-tech text-[10px] uppercase tracking-wider text-faint">
        <span>
          Depth: {depth}
        </span>

        <span>·</span>

        <span>
          {visibleNodes.length} nodes
        </span>

        <span>·</span>

        <span>
          {visibleEdges.length} edges
        </span>

        {data?.metadata?.generated_at && (
          <>
            <span>·</span>

            <span>
              Updated{' '}
              {new Date(
                data.metadata.generated_at,
              ).toLocaleTimeString()}
            </span>
          </>
        )}
      </div>
    </div>
  );
}
