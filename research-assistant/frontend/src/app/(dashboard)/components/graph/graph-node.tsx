"use client";

import {
  Handle,
  Position,
  type NodeProps,
} from "@xyflow/react";

import {
  FileText,
  FolderOpen,
  Hash,
  Network,
  Search,
  Tag,
} from "lucide-react";

import type { GraphNode as GraphNodeType } from "@/graph/types";

interface GraphNodeData extends GraphNodeType {
  selected?: boolean;
}

const iconMap = {
  paper: FileText,
  document: FileText,
  topic: Tag,
  author: Hash,
  dataset: FolderOpen,
  concept: Network,
  query: Search,
};

export function GraphNode({
  data,
}: NodeProps) {
  const node = data as unknown as GraphNodeData;

  const nodeType =
    typeof node.type === "string"
      ? node.type.toLowerCase()
      : "document";

  const Icon =
    iconMap[nodeType as keyof typeof iconMap] ?? FileText;

  return (
    <div
      className={[
        "min-w-[180px] max-w-[260px]",
        "rounded-lg border bg-zinc-950",
        "shadow-xl transition-all duration-150",
        node.selected
          ? "border-blue-500/80 shadow-blue-500/10"
          : "border-white/10 hover:border-white/20",
      ].join(" ")}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-2 !border-zinc-950 !bg-zinc-500"
      />

      <div className="flex items-center gap-3 border-b border-white/10 px-3 py-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white/5">
          <Icon className="h-4 w-4 text-zinc-300" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
            {nodeType}
          </div>

          <div className="truncate text-sm font-medium text-zinc-100">
            {node.label ?? node.name ?? node.id}
          </div>
        </div>
      </div>

      {(node.description || node.metadata) && (
        <div className="px-3 py-2.5">
          {node.description && (
            <p className="line-clamp-2 text-xs leading-relaxed text-zinc-500">
              {node.description}
            </p>
          )}

          {node.metadata &&
            typeof node.metadata === "object" &&
            Object.keys(node.metadata).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {Object.entries(node.metadata)
                  .slice(0, 3)
                  .map(([key, value]) => (
                    <span
                      key={key}
                      className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-zinc-500"
                    >
                      {key}: {String(value)}
                    </span>
                  ))}
              </div>
            )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-2 !border-zinc-950 !bg-zinc-500"
      />
    </div>
  );
}