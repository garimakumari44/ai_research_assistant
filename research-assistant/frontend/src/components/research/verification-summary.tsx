import {
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import type {
  VerificationSummary as VerificationSummaryType,
} from "@/research/types";

export function VerificationSummary({
  verification,
}: {
  verification: VerificationSummaryType;
}) {
  const status = verification.status ?? "failed";

  const verified = status === "verified";
  const partial = status === "partial";

  const confidence = verification.confidence ?? 0;

  const verifiedClaims =
    verification.verifiedClaims ?? 0;

  const totalClaims =
    verification.totalClaims ?? 0;

  const checks =
    verification.checks ?? [];

  const notes =
    verification.notes ?? [];

  return (
    <section className="rounded-2xl border">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4" />

          <h2 className="text-sm font-semibold">
            Verification
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {verified ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : partial ? (
            <AlertTriangle className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}

          <span className="text-xs font-medium capitalize">
            {status}
          </span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid gap-3 p-4 sm:grid-cols-3">
        <Metric
          label="Confidence"
          value={`${Math.round(
            confidence * 100,
          )}%`}
        />

        <Metric
          label="Verified claims"
          value={`${verifiedClaims}/${totalClaims}`}
        />

        <Metric
          label="Verification"
          value={
            verified
              ? "Passed"
              : partial
                ? "Partial"
                : "Failed"
          }
        />
      </div>

      {/* Verification Checks */}
      {checks.length > 0 && (
        <div className="border-t p-4">
          <div className="space-y-2">
            {checks.map((check, index) => {
              const checkId =
                check.id ??
                `${check.claim ?? check.name ?? "check"}-${index}`;

              const checkStatus =
                check.status ?? "failed";

              const checkConfidence =
                check.confidence ?? 0;

              const checkClaim =
                check.claim ??
                check.label ??
                check.name ??
                "Verification check";

              const checkExplanation =
                check.explanation ??
                check.message ??
                check.details;

              return (
                <div
                  key={checkId}
                  className="rounded-xl border p-3"
                >
                  <div className="flex items-start gap-2">
                    {checkStatus === "verified" ||
                    checkStatus === "passed" ? (
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    ) : checkStatus === "partial" ? (
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    ) : (
                      <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    )}

                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium">
                        {checkClaim}
                      </p>

                      {checkExplanation && (
                        <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                          {checkExplanation}
                        </p>
                      )}
                    </div>

                    <span className="ml-auto shrink-0 text-[10px] text-muted-foreground">
                      {Math.round(
                        checkConfidence * 100,
                      )}
                      %
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Notes */}
      {notes.length > 0 && (
        <div className="border-t p-4">
          <p className="text-xs font-semibold">
            Notes
          </p>

          <ul className="mt-2 space-y-1">
            {notes.map((note, index) => (
              <li
                key={`${note}-${index}`}
                className="text-xs text-muted-foreground"
              >
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border p-3">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold">
        {value}
      </p>
    </div>
  );
}