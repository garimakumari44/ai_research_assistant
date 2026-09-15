"use client";

import {
  CheckCircle2,
  Clock3,
  Sparkles,
} from "lucide-react";

import type {
  GenerationResponse,
} from "@/generation/types";

import CitationList from "./citation-list";
import ClaimVerification from "./claim-verification";
import EvidenceCitation from "./evidence-citation";
import VerificationSummary from "./verification-summary";

interface ResearchAnswerProps {
  response: GenerationResponse | null;
  showClaims?: boolean;
  showEvidence?: boolean;
  showCitations?: boolean;
  showVerification?: boolean;
}

function formatLatency(latency?: number) {
  if (latency === undefined) {
    return null;
  }

  if (latency < 1000) {
    return `${Math.round(latency)} ms`;
  }

  return `${(latency / 1000).toFixed(2)} s`;
}

export function ResearchAnswer({
  response,
  showClaims = true,
  showEvidence = true,
  showCitations = true,
  showVerification = true,
}: ResearchAnswerProps) {
  if (!response) {
    return (
      <div className="rounded-2xl border border-dashed border-border/70 bg-muted/10 p-8 text-center">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
          <Sparkles className="h-5 w-5" />
        </div>

        <h3 className="mt-3 text-sm font-semibold">
          No research answer yet
        </h3>

        <p className="mx-auto mt-1 max-w-md text-xs leading-5 text-muted-foreground">
          Ask a research question to generate an
          evidence-backed answer.
        </p>
      </div>
    );
  }

  const latency = formatLatency(
    response.usage?.latency_ms,
  );

  const claims =
    response.verification?.claims ?? [];

  const citations = response.citations ?? [];

  return (
    <article className="space-y-6">
      {/* Answer */}
      <section className="rounded-2xl border border-border/60 bg-card">
        <div className="border-b border-border/60 p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-muted">
              <Sparkles className="h-4 w-4" />
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold">
                  {response.title || "Research Answer"}
                </h2>

                {response.status === "completed" && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 text-[10px] font-medium">
                    <CheckCircle2 className="h-3 w-3" />
                    Complete
                  </span>
                )}
              </div>

              <div className="mt-1 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
                {response.model && (
                  <span>
                    Model: {response.model}
                  </span>
                )}

                {latency && (
                  <span className="inline-flex items-center gap-1">
                    <Clock3 className="h-3 w-3" />
                    {latency}
                  </span>
                )}

                {response.usage?.total_tokens !==
                  undefined && (
                  <span>
                    {response.usage.total_tokens} tokens
                  </span>
                )}
              </div>
            </div>

            {response.confidence !== undefined && (
              <div className="hidden text-right sm:block">
                <p className="text-lg font-bold">
                  {Math.round(
                    response.confidence * 100,
                  )}
                  %
                </p>

                <p className="text-[10px] text-muted-foreground">
                  confidence
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="p-5">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <div className="whitespace-pre-wrap text-sm leading-7 text-foreground">
              {response.answer}
            </div>
          </div>
        </div>
      </section>

      {/* Verification */}
      {showVerification &&
        response.verification && (
          <VerificationSummary
            verification={response.verification}
          />
        )}

      {/* Claims */}
      {showClaims && claims.length > 0 && (
        <section className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold">
              Claim Verification
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Each major claim is checked against retrieved
              evidence and linked citations.
            </p>
          </div>

          <div className="space-y-2">
            {claims.map((claim) => (
              <ClaimVerification
                key={claim.id}
                claim={claim}
                citations={citations}
              />
            ))}
          </div>
        </section>
      )}

      {/* Evidence → Citation */}
      {showEvidence && citations.length > 0 && (
        <section className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold">
              Evidence & Citations
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Supporting passages and the sources from which
              they were derived.
            </p>
          </div>

          <div className="space-y-2">
            {citations.map((citation, index) => (
              <EvidenceCitation
                key={citation.id}
                citation={citation}
                index={index}
              />
            ))}
          </div>
        </section>
      )}

      {/* Citation index */}
      {showCitations && citations.length > 0 && (
        <CitationList
          citations={citations}
          title="Source Citations"
        />
      )}

      {/* Generation error */}
      {response.error && (
        <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
          <p className="text-sm font-medium">
            Generation error
          </p>

          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            {response.error}
          </p>
        </div>
      )}
    </article>
  );
}

export default ResearchAnswer;