"use client";

import {
  FileText,
  FolderOpen,
  Hash,
  Network,
  Search,
  Tag,
} from "lucide-react";

const legendItems = [
  {
    type: "paper",
    label: "Paper",
    icon: FileText,
  },
  {
    type: "document",
    label: "Document",
    icon: FileText,
  },
  {
    type: "author",
    label: "Author",
    icon: Hash,
  },
  {
    type: "topic",
    label: "Topic",
    icon: Tag,
  },
  {
    type: "dataset",
    label: "Dataset",
    icon: FolderOpen,
  },
  {
    type: "concept",
    label: "Concept",
    icon: Network,
  },
  {
    type: "query",
    label: "Query",
    icon: Search,
  },
];

interface GraphLegendProps {
  items?: typeof legendItems;
}

export function GraphLegend({
  items = legendItems,
}: GraphLegendProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950 p-3">
      <div className="mb-3 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
        Node types
      </div>

      <div className="grid grid-cols-2 gap-2">
        {items.map(({ type, label, icon: Icon }) => (
          <div
            key={type}
            className="flex items-center gap-2 text-xs text-zinc-500"
          >
            <Icon className="h-3.5 w-3.5 text-zinc-400" />

            <span>{label}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 border-t border-white/5 pt-3">
        <div className="flex items-center gap-2 text-[10px] text-zinc-600">
          <span className="h-px w-6 bg-zinc-600" />
          Relationship
        </div>

        <div className="mt-2 flex items-center gap-2 text-[10px] text-zinc-600">
          <span className="h-px w-6 bg-zinc-400" />
          Selected relationship
        </div>
      </div>
    </div>
  );
}