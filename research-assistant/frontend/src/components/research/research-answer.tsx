
import {
  CheckCircle2,
  Sparkles,
} from "lucide-react";

import type {
  ResearchAnswer as ResearchAnswerType,
} from "@/research/types";

import { CitationList } from "./citation-list";
import { EvidenceList } from "./evidence-list";
import { VerificationSummary } from "./verification-summary";

export function ResearchAnswer({
  answer,
}: {
  answer?: ResearchAnswerType;
}) {
  if (!answer) {
    return null;
  }

  return (
    <section className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* Main Answer                                                        */}
      {/* ------------------------------------------------------------------ */}

      <div className="overflow-hidden rounded-2xl border bg-background shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>

            <div>
              <h2 className="text-sm font-semibold tracking-tight">
                Research Answer
              </h2>

              <p className="mt-0.5 text-[11px] text-muted-foreground">
                AI-generated synthesis from retrieved evidence
              </p>
            </div>
          </div>

          {answer.confidence !== undefined && (
            <div className="flex items-center gap-1.5 rounded-full border bg-muted/40 px-2.5 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />

              <span className="text-[10px] font-medium text-muted-foreground">
                {Math.round(answer.confidence * 100)}% confidence
              </span>
            </div>
          )}
        </div>

        {/* Executive Summary */}
        {answer.summary && (
          <div className="border-b bg-muted/20 px-5 py-4">
            <div className="mb-1.5 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Executive Summary
              </span>
            </div>

            <p className="max-w-4xl text-sm leading-6 text-foreground/85">
              {answer.summary}
            </p>
          </div>
        )}

        {/* Generated Answer */}
        <div className="px-5 py-6 sm:px-7 sm:py-7">
          <article className="max-w-4xl">
            <div className="whitespace-pre-wrap text-[14px] leading-7 text-foreground/90">
              {answer.answer}
            </div>
          </article>
        </div>

        {/* Grounding Footer */}
        <div className="flex items-center gap-2 border-t bg-muted/10 px-5 py-3">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />

          <span className="text-[10px] font-medium text-muted-foreground">
            Grounded research response
          </span>

          <span className="text-[10px] text-muted-foreground/50">
            •
          </span>

          <span className="text-[10px] text-muted-foreground">
            Evidence-backed
          </span>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Supporting Research                                                */}
      {/* ------------------------------------------------------------------ */}

      <EvidenceList
        evidence={answer.evidence}
      />

      <CitationList
        citations={answer.citations}
      />

      {answer.verification && (
        <VerificationSummary
          verification={answer.verification}
        />
      )}
    </section>
  );
}

