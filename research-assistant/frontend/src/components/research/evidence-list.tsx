"use client";

import {
  GitBranch,
  KeyRound,
  Search,
} from "lucide-react";

import type {
  Evidence,
  EvidenceSourceType,
} from "@/research/types";

import { EvidenceCard } from "./evidence-card";

const groups: {
  type: EvidenceSourceType;
  label: string;
  icon: typeof Search;
}[] = [
  {
    type: "semantic",
    label: "Semantic Evidence",
    icon: Search,
  },
  {
    type: "keyword",
    label: "Keyword Evidence",
    icon: KeyRound,
  },
  {
    type: "graph",
    label: "Graph Evidence",
    icon: GitBranch,
  },
];

export function EvidenceList({
  evidence,
}: {
  evidence: Evidence[];
}) {
  if (!evidence.length) {
    return null;
  }

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-sm font-semibold">
          Evidence
        </h2>

        <p className="mt-1 text-xs text-muted-foreground">
          Evidence collected from semantic, keyword, and research-graph retrieval.
        </p>
      </div>

      <div className="space-y-6">
        {groups.map((group) => {
          const items =
            evidence.filter(
              (item) =>
                item.sourceType ===
                group.type,
            );

          if (!items.length) {
            return null;
          }

          const Icon = group.icon;

          return (
            <div key={group.type}>
              <div className="mb-2 flex items-center gap-2">
                <Icon className="h-3.5 w-3.5" />

                <span className="text-xs font-semibold">
                  {group.label}
                </span>

                <span className="rounded-full border px-1.5 py-0.5 text-[9px]">
                  {items.length}
                </span>
              </div>

              <div className="space-y-2">
                {items.map(
                  (item) => (
                    <EvidenceCard
                      key={item.id}
                      evidence={item}
                    />
                  ),
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}