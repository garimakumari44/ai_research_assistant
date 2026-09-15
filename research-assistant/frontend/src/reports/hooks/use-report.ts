"use client";

import { useQuery } from "@tanstack/react-query";

import { getReport } from "../api";

import type { Report } from "../types";

/**
 * Fetch a single report by ID.
 */
export function useReport(
  reportId: string | undefined,
) {
  return useQuery<Report>({
    queryKey: ["reports", "detail", reportId],

    queryFn: () => {
      if (!reportId) {
        throw new Error("Report ID is required.");
      }

      return getReport(reportId);
    },

    enabled: Boolean(reportId),
  });
}