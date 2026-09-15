"use client";

import { useCallback, useState } from "react";

import { startResearch } from "../api";

import type {
  ResearchReport,
  ResearchRequest,
} from "../types";

/* -------------------------------------------------------------------------- */
/* API response                                                               */
/* -------------------------------------------------------------------------- */

type ResearchApiResponse =
  | ResearchReport
  | {
      report?: ResearchReport | null;
      execution_id?: string;
      research_execution_id?: string;
      status?: string;
      message?: string;
    };

/* -------------------------------------------------------------------------- */
/* Hook                                                                       */
/* -------------------------------------------------------------------------- */

export function useResearch() {
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ------------------------------------------------------------------------ */
  /* Run research                                                             */
  /* ------------------------------------------------------------------------ */

  const runResearch = useCallback(
    async (
      request: ResearchRequest,
    ): Promise<ResearchReport> => {
      const question = request.question?.trim();

      if (!question || question.length < 3) {
        const message = "A research question is required.";

        setError(message);

        throw new Error(message);
      }

      setLoading(true);
      setError(null);

      try {
        const response = (await startResearch({
          ...request,
          question,
        })) as ResearchApiResponse;

        /* ------------------------------------------------------------------ */
        /* Direct ResearchReport response                                     */
        /* ------------------------------------------------------------------ */

        if (
          response &&
          typeof response === "object" &&
          "sections" in response
        ) {
          const researchReport = response as ResearchReport;

          setReport(researchReport);

          return researchReport;
        }

        /* ------------------------------------------------------------------ */
        /* Wrapped ResearchReport response                                    */
        /* ------------------------------------------------------------------ */

        if (
          response &&
          typeof response === "object" &&
          "report" in response &&
          response.report
        ) {
          setReport(response.report);

          return response.report;
        }

        /* ------------------------------------------------------------------ */
        /* Execution-style response                                           */
        /* ------------------------------------------------------------------ */

        if (response && typeof response === "object") {
          const executionId =
            "execution_id" in response
              ? response.execution_id
              : "research_execution_id" in response
                ? response.research_execution_id
                : undefined;

          const status =
            "status" in response
              ? response.status
              : undefined;

          const message =
            "message" in response
              ? response.message
              : undefined;

          const executionMessage = executionId
            ? `Research execution started successfully. Execution ID: ${executionId}.`
            : message ??
              (status
                ? `Research execution started with status: ${status}.`
                : "Research execution started, but no report was returned.");

          throw new Error(executionMessage);
        }

        throw new Error(
          "Invalid response received from the research API.",
        );
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Research execution failed.";

        setError(message);

        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  /* ------------------------------------------------------------------------ */
  /* Clear research state                                                     */
  /* ------------------------------------------------------------------------ */

  const clear = useCallback(() => {
    setReport(null);
    setError(null);
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Public API                                                               */
  /* ------------------------------------------------------------------------ */

  return {
    report,
    loading,
    error,
    runResearch,
    clear,
  };
}