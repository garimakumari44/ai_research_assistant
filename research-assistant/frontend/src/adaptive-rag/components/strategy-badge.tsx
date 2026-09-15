"use client";

import {
  BrainCircuit,
  GitBranch,
  Layers3,
  RefreshCw,
  Search,
  ShieldCheck,
  Zap,
} from "lucide-react";

import type { RAGStrategy } from "../types";

interface StrategyBadgeProps {
  strategy: RAGStrategy | string;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
  className?: string;
}

const STRATEGY_CONFIG: Record<
  string,
  {
    label: string;
    icon: typeof Zap;
    description: string;
  }
> = {
  direct: {
    label: "Direct",
    icon: Zap,
    description: "Single-pass retrieval and generation",
  },
  iterative: {
    label: "Iterative",
    icon: RefreshCw,
    description: "Multiple retrieval and reasoning cycles",
  },
  multi_query: {
    label: "Multi-Query",
    icon: Search,
    description: "Generates multiple search perspectives",
  },
  corrective: {
    label: "Corrective",
    icon: ShieldCheck,
    description: "Evaluates and corrects weak evidence",
  },
  graph_augmented: {
    label: "Graph Augmented",
    icon: GitBranch,
    description: "Combines retrieval with graph relationships",
  },
};

export function StrategyBadge({
  strategy,
  size = "md",
  showIcon = true,
  className = "",
}: StrategyBadgeProps) {
  const normalized = String(strategy).toLowerCase();
  const config = STRATEGY_CONFIG[normalized] ?? {
    label: strategy,
    icon: BrainCircuit,
    description: "Adaptive retrieval strategy",
  };

  const Icon = config.icon;

  const sizeClasses = {
    sm: "px-2 py-1 text-xs gap-1",
    md: "px-2.5 py-1.5 text-sm gap-1.5",
    lg: "px-3 py-2 text-sm gap-2",
  };

  return (
    <span
      title={config.description}
      className={[
        "inline-flex items-center rounded-md border",
        "border-slate-700 bg-slate-900/70",
        "font-medium text-slate-200",
        sizeClasses[size],
        className,
      ].join(" ")}
    >
      {showIcon && <Icon className="h-3.5 w-3.5 text-cyan-400" />}
      <span>{config.label}</span>
    </span>
  );
}

export default StrategyBadge;