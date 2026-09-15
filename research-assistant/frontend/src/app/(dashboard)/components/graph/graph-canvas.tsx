"use client";

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Connection,
  type Edge,
  type Node,
  type OnEdgesChange,
  type OnNodesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useCallback, useMemo } from "react";

import type { GraphEdge, GraphNode } from "@/graph/types";

import { GraphControls } from "./graph-controls";
import { GraphEdge as GraphEdgeComponent } from "./graph-edge";
import { GraphNode as GraphNodeComponent } from "./graph-node";

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];

  onNodesChange?: OnNodesChange;
  onEdgesChange?: OnEdgesChange;
  onConnect?: (connection: Connection) => void;

  selectedNodeId?: string | null;
  onNodeSelect?: (node: GraphNode | null) => void;

  className?: string;
}

export function GraphCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  selectedNodeId,
  onNodeSelect,
  className,
}: GraphCanvasProps) {
  const flowNodes = useMemo<Node[]>(
    () =>
      nodes.map((node) => ({
        id: node.id,
        type: "graphNode",
        position: node.position ?? { x: 0, y: 0 },
        data: {
          ...node,
          selected: node.id === selectedNodeId,
        },
      })),
    [nodes, selectedNodeId],
  );

  const flowEdges = useMemo<Edge[]>(
    () =>
      edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: "graphEdge",
        animated: edge.animated ?? false,
        data: edge,
      })),
    [edges],
  );

  const nodeTypes = useMemo(
    () => ({
      graphNode: GraphNodeComponent,
    }),
    [],
  );

  const edgeTypes = useMemo(
    () => ({
      graphEdge: GraphEdgeComponent,
    }),
    [],
  );

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const graphNode = nodes.find((item) => item.id === node.id) ?? null;
      onNodeSelect?.(graphNode);
    },
    [nodes, onNodeSelect],
  );

  const handlePaneClick = useCallback(() => {
    onNodeSelect?.(null);
  }, [onNodeSelect]);

  return (
    <div
      className={[
        "relative h-full min-h-[600px] w-full overflow-hidden rounded-xl",
        "border border-white/10 bg-black",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <ReactFlowProvider>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          onPaneClick={handlePaneClick}
          fitView
          fitViewOptions={{
            padding: 0.2,
            maxZoom: 1.25,
          }}
          minZoom={0.15}
          maxZoom={2}
          defaultEdgeOptions={{
            type: "graphEdge",
          }}
          proOptions={{
            hideAttribution: true,
          }}
        >
          <Background
            gap={24}
            size={1}
            className="opacity-30"
          />

          <MiniMap
            pannable
            zoomable
            nodeStrokeWidth={2}
            className="!border !border-white/10 !bg-black/80"
          />

          <Controls
            showInteractive={false}
            className="!border !border-white/10 !bg-black/80"
          />
        </ReactFlow>

        <GraphControls />
      </ReactFlowProvider>
    </div>
  );
}