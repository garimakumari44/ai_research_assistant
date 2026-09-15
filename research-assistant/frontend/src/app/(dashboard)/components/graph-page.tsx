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

/**
 * ---------------------------------------------------------
 * Graph Page
 * ---------------------------------------------------------
 *
 * ReactFlowProvider must be an ancestor of every component
 * that uses React Flow hooks such as useReactFlow().
 *
 * GraphControls uses useReactFlow(), so the provider wraps
 * GraphPageContent rather than being placed inside it.
 */
export function GraphPage() {
  return (
    <ReactFlowProvider>
      <GraphPageContent />
    </ReactFlowProvider>
  );
}

/**
 * ---------------------------------------------------------
 * Graph Page Content
 * ---------------------------------------------------------
 */
function GraphPageContent() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    null,
  );

  const [nodeType, setNodeType] = useState<GraphNodeType | 'all'>('all');

  const [edgeType, setEdgeType] = useState<GraphEdgeType | 'all'>('all');

  const [search, setSearch] = useState('');

  const [depth, setDepth] = useState(2);

  const [filters, setFilters] = useState<GraphFiltersState>({
    nodeTypes: [],
    edgeTypes: [],
    minRelevance: 0,
  });

  /**
   * ---------------------------------------------------------
   * Graph data
   * ---------------------------------------------------------
   */
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

  /**
   * ---------------------------------------------------------
   * Available filter values
   * ---------------------------------------------------------
   */
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

  /**
   * ---------------------------------------------------------
   * Visible nodes
   * ---------------------------------------------------------
   */
  const visibleNodes = useMemo(() => {
    let result = nodes;

    /**
     * Legacy single node-type filter
     */
    if (nodeType !== 'all') {
      result = result.filter(
        (node) => node.type === nodeType,
      );
    }

    /**
     * Multi-select node-type filter
     *
     * If nothing is selected, show all types.
     */
    if (filters.nodeTypes.length > 0) {
      result = result.filter((node) =>
        filters.nodeTypes.includes(node.type),
      );
    }

    /**
     * Minimum relevance filter
     *
     * Only apply if the node has a relevance field.
     */
    if (
      filters.minRelevance &&
      filters.minRelevance > 0
    ) {
      result = result.filter((node) => {
        const relevance =
          typeof (
            node as GraphNode & {
              relevance?: number;
            }
          ).relevance === 'number'
            ? (
                node as GraphNode & {
                  relevance?: number;
                }
              ).relevance
            : 1;

        return relevance >= filters.minRelevance!;
      });
    }

    return result;
  }, [
    nodes,
    nodeType,
    filters.nodeTypes,
    filters.minRelevance,
  ]);

  /**
   * ---------------------------------------------------------
   * Visible node IDs
   * ---------------------------------------------------------
   */
  const visibleNodeIds = useMemo(
    () =>
      new Set(
        visibleNodes.map((node) => node.id),
      ),
    [visibleNodes],
  );

  /**
   * ---------------------------------------------------------
   * Visible edges
   * ---------------------------------------------------------
   */
  const visibleEdges = useMemo(() => {
    return edges.filter((edge) => {
      /**
       * Only keep edges where both connected nodes
       * are currently visible.
       */
      const nodesVisible =
        visibleNodeIds.has(edge.source) &&
        visibleNodeIds.has(edge.target);

      if (!nodesVisible) {
        return false;
      }

      /**
       * Legacy single edge-type filter
       */
      if (
        edgeType !== 'all' &&
        edge.type !== edgeType
      ) {
        return false;
      }

      /**
       * Multi-select edge-type filter
       */
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

  /**
   * ---------------------------------------------------------
   * Selected node
   * ---------------------------------------------------------
   */
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

  /**
   * ---------------------------------------------------------
   * Selected connections
   * ---------------------------------------------------------
   */
  const selectedConnections = useMemo(() => {
    if (!selectedNodeId) {
      return [];
    }

    return visibleEdges.filter(
      (edge) =>
        edge.source === selectedNodeId ||
        edge.target === selectedNodeId,
    );
  }, [
    selectedNodeId,
    visibleEdges,
  ]);

  /**
   * ---------------------------------------------------------
   * Node selection
   * ---------------------------------------------------------
   */
  const handleSelectNode = (node: GraphNode) => {
    setSelectedNodeId(node.id);
  };

  const handleClearSelection = () => {
    setSelectedNodeId(null);
  };

  /**
   * ---------------------------------------------------------
   * Filter changes
   * ---------------------------------------------------------
   */
  const handleFiltersChange = (
    nextFilters: GraphFiltersState,
  ) => {
    setFilters(nextFilters);

    /**
     * Keep the existing backend query filters synchronized
     * with the filter UI.
     *
     * A single selected type can be sent to the backend.
     * Multiple selected types remain frontend filters.
     */
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

  /**
   * ---------------------------------------------------------
   * Render
   * ---------------------------------------------------------
   */
  return (
    <div className="mx-auto max-w-[1600px] px-6 py-8 md:px-10">
      {/* -------------------------------------------------- */}
      {/* Header */}
      {/* -------------------------------------------------- */}

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

      {/* -------------------------------------------------- */}
      {/* Filters */}
      {/* -------------------------------------------------- */}

      <GraphFilters
        filters={filters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onChange={handleFiltersChange}
      />

      {/* -------------------------------------------------- */}
      {/* Main Content */}
      {/* -------------------------------------------------- */}

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
        {/* ------------------------------------------------ */}
        {/* Graph */}
        {/* ------------------------------------------------ */}

        <div className="relative min-h-[650px] overflow-hidden rounded-lg border border-border bg-surface">
          {/* ---------------------------------------------- */}
          {/* Loading */}
          {/* ---------------------------------------------- */}

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

          {/* ---------------------------------------------- */}
          {/* Error */}
          {/* ---------------------------------------------- */}

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

          {/* ---------------------------------------------- */}
          {/* Empty State */}
          {/* ---------------------------------------------- */}

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

          {/* ---------------------------------------------- */}
          {/* Graph Canvas */}
          {/* ---------------------------------------------- */}

          <GraphCanvas
            nodes={visibleNodes}
            edges={visibleEdges}
            selectedNodeId={selectedNodeId}
            onNodeSelect={handleSelectNode}
          />

          {/* ---------------------------------------------- */}
          {/* Legend */}
          {/* ---------------------------------------------- */}

          <GraphLegend />

          {/* ---------------------------------------------- */}
          {/* Controls */}
          {/* ---------------------------------------------- */}

          <GraphControls
            depth={depth}
            onDepthChange={setDepth}
          />
        </div>

        {/* ------------------------------------------------ */}
        {/* Details */}
        {/* ------------------------------------------------ */}

        <GraphDetails
          node={selectedNode}
          connections={selectedConnections}
          onClose={handleClearSelection}
        />
      </div>

      {/* -------------------------------------------------- */}
      {/* Graph Metadata */}
      {/* -------------------------------------------------- */}

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