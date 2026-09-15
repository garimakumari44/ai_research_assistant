"use client";

import {
  ExternalLink,
  FileText,
  X,
} from "lucide-react";

import type { GraphNode } from "@/graph/types";

interface GraphDetailsProps {
  node: GraphNode | null;
  onClose?: () => void;
  onOpen?: (node: GraphNode) => void;
}

export function GraphDetails({
  node,
  onClose,
  onOpen,
}: GraphDetailsProps) {
  if (!node) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-white/10 bg-zinc-950 p-6">
        <div className="text-center">
          <FileText className="mx-auto mb-3 h-5 w-5 text-zinc-700" />

          <p className="text-xs text-zinc-600">
            Select a graph node to inspect its details.
          </p>
        </div>
      </div>
    );
  }

  const metadata =
    node.metadata &&
    typeof node.metadata === "object"
      ? Object.entries(node.metadata)
      : [];

  return (
    <aside className="h-full overflow-y-auto rounded-lg border border-white/10 bg-zinc-950">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-600">
            {node.type}
          </div>

          <h3 className="mt-0.5 truncate text-sm font-medium text-zinc-100">
            {node.label ?? node.name ?? node.id}
          </h3>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close details"
            className="rounded-md p-1.5 text-zinc-600 hover:bg-white/5 hover:text-zinc-300"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="space-y-5 p-4">
        {node.description && (
          <section>
            <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              Description
            </div>

            <p className="text-xs leading-relaxed text-zinc-400">
              {node.description}
            </p>
          </section>
        )}

        <section>
          <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
            Node ID
          </div>

          <code className="break-all text-xs text-zinc-500">
            {node.id}
          </code>
        </section>

        {metadata.length > 0 && (
          <section>
            <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              Metadata
            </div>

            <div className="space-y-2">
              {metadata.map(([key, value]) => (
                <div
                  key={key}
                  className="flex justify-between gap-4 border-b border-white/5 pb-2"
                >
                  <span className="text-xs text-zinc-600">
                    {key}
                  </span>

                  <span className="max-w-[60%] break-words text-right text-xs text-zinc-400">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {onOpen && (
          <button
            type="button"
            onClick={() => onOpen(node)}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-zinc-300 transition hover:bg-white/10 hover:text-white"
          >
            Open source
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </aside>
  );
}