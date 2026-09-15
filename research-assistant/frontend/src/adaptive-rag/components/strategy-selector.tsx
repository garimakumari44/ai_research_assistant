"use client";

import {
  BrainCircuit,
  GitBranch,
  RefreshCw,
  Search,
  ShieldCheck,
  Zap,
} from "lucide-react";

import type { RAGStrategy } from "../types";

interface StrategySelectorProps {
  value?: RAGStrategy | string;
  onChange: (strategy: RAGStrategy | string) => void;
  disabled?: boolean;
  allowAutomatic?: boolean;
  className?: string;
}

const STRATEGIES = [
  {
    value: "direct",
    label: "Direct",
    description: "Fast single-pass retrieval",
    icon: Zap,
  },
  {
    value: "iterative",
    label: "Iterative",
    description: "Repeated retrieval and reasoning",
    icon: RefreshCw,
  },
  {
    value: "multi_query",
    label: "Multi-Query",
    description: "Search from multiple perspectives",
    icon: Search,
  },
  {
    value: "corrective",
    label: "Corrective",
    description: "Evaluate and repair weak evidence",
    icon: ShieldCheck,
  },
  {
    value: "graph_augmented",
    label: "Graph Augmented",
    description: "Use graph relationships with retrieval",
    icon: GitBranch,
  },
];

export function StrategySelector({
  value = "auto",
  onChange,
  disabled = false,
  allowAutomatic = true,
  className = "",
}: StrategySelectorProps) {
  const options = allowAutomatic
    ? [
        {
          value: "auto",
          label: "Adaptive",
          description: "Let the controller choose",
          icon: BrainCircuit,
        },
        ...STRATEGIES,
      ]
    : STRATEGIES;

  return (
    <div className={className}>
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-slate-200">
          Retrieval Strategy
        </h3>

        <p className="mt-1 text-xs text-slate-500">
          Choose how the RAG controller should approach the query.
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((option) => {
          const Icon = option.icon;
          const selected = value === option.value;

          return (
            <button
              key={option.value}
              type="button"
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={[
                "group rounded-lg border p-3 text-left transition",
                selected
                  ? "border-cyan-500/50 bg-cyan-500/10"
                  : "border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-900/70",
                disabled
                  ? "cursor-not-allowed opacity-50"
                  : "cursor-pointer",
              ].join(" ")}
            >
              <div className="flex items-start gap-3">
                <div
                  className={[
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
                    selected
                      ? "bg-cyan-500/15 text-cyan-400"
                      : "bg-slate-900 text-slate-500 group-hover:text-slate-300",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4" />
                </div>

                <div className="min-w-0">
                  <div
                    className={[
                      "text-sm font-medium",
                      selected
                        ? "text-cyan-300"
                        : "text-slate-200",
                    ].join(" ")}
                  >
                    {option.label}
                  </div>

                  <p className="mt-1 text-xs leading-4 text-slate-500">
                    {option.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default StrategySelector;