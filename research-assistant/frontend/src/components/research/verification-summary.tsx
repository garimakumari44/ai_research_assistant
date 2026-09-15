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
  const verified =
    verification.status ===
    "verified";

  const partial =
    verification.status ===
    "partial";

  return (
    <section className="rounded-2xl border">
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
            {verification.status}
          </span>
        </div>
      </div>

      <div className="grid gap-3 p-4 sm:grid-cols-3">
        <Metric
          label="Confidence"
          value={`${Math.round(
            verification.confidence *
              100,
          )}%`}
        />

        <Metric
          label="Verified claims"
          value={`${verification.verifiedClaims}/${verification.totalClaims}`}
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

      {verification.checks.length >
        0 && (
        <div className="border-t p-4">
          <div className="space-y-2">
            {verification.checks.map(
              (check) => (
                <div
                  key={check.id}
                  className="rounded-xl border p-3"
                >
                  <div className="flex items-start gap-2">
                    {check.status ===
                    "verified" ? (
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    ) : check.status ===
                      "partial" ? (
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    ) : (
                      <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    )}

                    <div className="min-w-0">
                      <p className="text-xs font-medium">
                        {check.claim}
                      </p>

                      {check.explanation && (
                        <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                          {
                            check.explanation
                          }
                        </p>
                      )}
                    </div>

                    <span className="ml-auto text-[10px] text-muted-foreground">
                      {Math.round(
                        check.confidence *
                          100,
                      )}
                      %
                    </span>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>
      )}

      {verification.notes &&
        verification.notes.length >
          0 && (
          <div className="border-t p-4">
            <p className="text-xs font-semibold">
              Notes
            </p>

            <ul className="mt-2 space-y-1">
              {verification.notes.map(
                (note) => (
                  <li
                    key={note}
                    className="text-xs text-muted-foreground"
                  >
                    {note}
                  </li>
                ),
              )}
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