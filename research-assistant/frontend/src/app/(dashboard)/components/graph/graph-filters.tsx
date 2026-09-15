"use client";

import { SlidersHorizontal } from "lucide-react";

export interface GraphFiltersState {
  nodeTypes: string[];
  edgeTypes: string[];
  minRelevance?: number;
}

interface GraphFiltersProps {
  filters: GraphFiltersState;
  availableNodeTypes?: string[];
  availableEdgeTypes?: string[];
  onChange: (filters: GraphFiltersState) => void;
}

export function GraphFilters({
  filters,
  availableNodeTypes = [],
  availableEdgeTypes = [],
  onChange,
}: GraphFiltersProps) {
  const toggleValue = (
    key: "nodeTypes" | "edgeTypes",
    value: string,
  ) => {
    const current = filters[key] ?? [];

    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];

    onChange({
      ...filters,
      [key]: next,
    });
  };

  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950 p-3">
      <div className="mb-3 flex items-center gap-2">
        <SlidersHorizontal className="h-4 w-4 text-zinc-400" />

        <span className="text-xs font-medium text-zinc-200">
          Graph filters
        </span>
      </div>

      <div className="space-y-4">
        {/* Node Types */}
        <div>
          <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
            Node types
          </div>

          <div className="flex flex-wrap gap-1.5">
            {availableNodeTypes.map((type) => {
              const active = (filters.nodeTypes ?? []).includes(type);

              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleValue("nodeTypes", type)}
                  className={[
                    "rounded-md border px-2 py-1 text-[11px] transition",
                    active
                      ? "border-blue-500/40 bg-blue-500/10 text-blue-400"
                      : "border-white/10 bg-white/[0.02] text-zinc-500 hover:text-zinc-300",
                  ].join(" ")}
                >
                  {type}
                </button>
              );
            })}

            {availableNodeTypes.length === 0 && (
              <span className="text-[11px] text-zinc-600">
                No node types available
              </span>
            )}
          </div>
        </div>

        {/* Edge Types */}
        <div>
          <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
            Relationships
          </div>

          <div className="flex flex-wrap gap-1.5">
            {availableEdgeTypes.map((type) => {
              const active = (filters.edgeTypes ?? []).includes(type);

              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleValue("edgeTypes", type)}
                  className={[
                    "rounded-md border px-2 py-1 text-[11px] transition",
                    active
                      ? "border-blue-500/40 bg-blue-500/10 text-blue-400"
                      : "border-white/10 bg-white/[0.02] text-zinc-500 hover:text-zinc-300",
                  ].join(" ")}
                >
                  {type}
                </button>
              );
            })}

            {availableEdgeTypes.length === 0 && (
              <span className="text-[11px] text-zinc-600">
                No relationships available
              </span>
            )}
          </div>
        </div>

        {/* Minimum Relevance */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              Minimum relevance
            </span>

            <span className="text-xs text-zinc-400">
              {filters.minRelevance ?? 0}
            </span>
          </div>

          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={filters.minRelevance ?? 0}
            onChange={(event) =>
              onChange({
                ...filters,
                minRelevance: Number(event.target.value),
              })
            }
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}