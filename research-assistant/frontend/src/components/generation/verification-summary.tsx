"use client";

import {
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";

import type { GenerationVerification } from "@/generation/types";

interface VerificationSummaryProps {
  verification: GenerationVerification;
}

export function VerificationSummary({
  verification,
}: VerificationSummaryProps) {
  const claims = verification.claims ?? [];

  const supported = claims.filter(
    (claim) => claim.supported,
  ).length;

  const unsupported = claims.length - supported;

  const supportRate =
    claims.length > 0
      ? supported / claims.length
      : 0;

  const confidence =
    verification.confidence !== undefined
      ? verification.confidence
      : supportRate;

  const confidencePercent = Math.round(
    confidence * 100,
  );

  return (
    <section className="rounded-2xl border border-border/60 bg-card p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-muted">
          <ShieldCheck className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold">
                Verification
              </h3>

              <p className="mt-1 text-xs text-muted-foreground">
                Claim-level verification against the available
                evidence.
              </p>
            </div>

            <div className="text-right">
              <p className="text-lg font-bold">
                {confidencePercent}%
              </p>

              <p className="text-[10px] text-muted-foreground">
                confidence
              </p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-lg bg-muted/40 p-3">
              <p className="text-lg font-semibold">
                {claims.length}
              </p>

              <p className="text-[10px] text-muted-foreground">
                Claims
              </p>
            </div>

            <div className="rounded-lg bg-muted/40 p-3">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" />

                <p className="text-lg font-semibold">
                  {supported}
                </p>
              </div>

              <p className="text-[10px] text-muted-foreground">
                Supported
              </p>
            </div>

            <div className="rounded-lg bg-muted/40 p-3">
              <div className="flex items-center gap-1.5">
                <AlertCircle className="h-3.5 w-3.5" />

                <p className="text-lg font-semibold">
                  {unsupported}
                </p>
              </div>

              <p className="text-[10px] text-muted-foreground">
                Unsupported
              </p>
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground">
                Claim support rate
              </span>

              <span className="font-medium">
                {Math.round(supportRate * 100)}%
              </span>
            </div>

            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-foreground transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(
                      0,
                      supportRate * 100,
                    ),
                  )}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default VerificationSummary;