"use client";

import {
  AlertCircle,
  CheckCircle2,
  CircleHelp,
  Link2,
} from "lucide-react";

import type {
  GenerationCitation,
  VerificationClaim,
} from "@/generation/types";

interface ClaimVerificationProps {
  claim: VerificationClaim;
  citations?: GenerationCitation[];
}

function getConfidenceLabel(confidence: number) {
  if (confidence >= 0.9) return "High confidence";
  if (confidence >= 0.7) return "Moderate confidence";
  if (confidence >= 0.5) return "Low confidence";

  return "Very low confidence";
}

export function ClaimVerification({
  claim,
  citations = [],
}: ClaimVerificationProps) {
  const relatedCitations = citations.filter((citation) =>
    claim.citation_ids?.includes(citation.id),
  );

  const confidencePercent = Math.round(
    claim.confidence * 100,
  );

  const StatusIcon = claim.supported
    ? CheckCircle2
    : confidencePercent >= 50
      ? CircleHelp
      : AlertCircle;

  return (
    <article className="rounded-xl border border-border/60 bg-card p-4">
      <div className="flex gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
          <StatusIcon className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          {/* Claim */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                Claim
              </p>

              <p className="text-sm font-medium leading-6">
                {claim.claim}
              </p>
            </div>

            <span className="shrink-0 rounded-full bg-muted px-2 py-1 text-[11px] font-medium">
              {claim.supported
                ? "Supported"
                : "Unsupported"}
            </span>
          </div>

          {/* Verification */}
          <div className="mt-4 border-t border-border/50 pt-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                Verification
              </span>

              <span className="text-xs font-semibold">
                {confidencePercent}%
              </span>
            </div>

            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-foreground transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(0, confidencePercent),
                  )}%`,
                }}
              />
            </div>

            <p className="mt-1 text-[11px] text-muted-foreground">
              {getConfidenceLabel(claim.confidence)}
            </p>

            {claim.explanation && (
              <p className="mt-3 text-xs leading-5 text-muted-foreground">
                {claim.explanation}
              </p>
            )}
          </div>

          {/* Evidence / Citation relationship */}
          {relatedCitations.length > 0 && (
            <div className="mt-4 border-t border-border/50 pt-3">
              <div className="mb-2 flex items-center gap-2">
                <Link2 className="h-3 w-3 text-muted-foreground" />

                <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Supporting citations
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                {relatedCitations.map((citation) => (
                  <span
                    key={citation.id}
                    className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-muted/30 px-2 py-1 text-[11px] text-muted-foreground"
                  >
                    <Link2 className="h-3 w-3" />

                    {citation.marker ||
                      citation.title ||
                      "Source"}
                  </span>
                ))}
              </div>
            </div>
          )}

          {relatedCitations.length === 0 && (
            <div className="mt-4 rounded-lg border border-dashed border-border/60 bg-muted/10 p-3">
              <p className="text-xs text-muted-foreground">
                No supporting citation was linked to this claim.
              </p>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

export default ClaimVerification;