"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createReport,
  deleteReport,
  generateReport,
  getReports,
  updateReport,
} from "../api";

import type {
  CreateReportRequest,
  Report,
  ReportListParams,
  UpdateReportRequest,
} from "../types";

/**
 * ---------------------------------------------------------------------------
 * QUERY KEYS
 * ---------------------------------------------------------------------------
 */

export const reportKeys = {
  all: ["reports"] as const,

  lists: () =>
    [...reportKeys.all, "list"] as const,

  list: (params?: ReportListParams) =>
    [
      ...reportKeys.lists(),
      params ?? {},
    ] as const,

  details: () =>
    [...reportKeys.all, "detail"] as const,

  detail: (reportId: number | string) =>
    [
      ...reportKeys.details(),
      String(reportId),
    ] as const,
};


/**
 * ---------------------------------------------------------------------------
 * LIST
 * ---------------------------------------------------------------------------
 */

export function useReports(
  params?: ReportListParams,
) {
  return useQuery({
    queryKey: reportKeys.list(params),

    queryFn: () =>
      getReports(params),
  });
}


/**
 * ---------------------------------------------------------------------------
 * CREATE
 * ---------------------------------------------------------------------------
 */

export function useCreateReport() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: CreateReportRequest,
    ) =>
      createReport(payload),

    onSuccess: (report: Report) => {
      /*
       * Refresh report history.
       */
      queryClient.invalidateQueries({
        queryKey: reportKeys.lists(),
      });

      /*
       * Put the newly-created report directly
       * into the detail cache.
       */
      queryClient.setQueryData(
        reportKeys.detail(report.id),
        report,
      );
    },
  });
}


/**
 * ---------------------------------------------------------------------------
 * GENERATE
 * ---------------------------------------------------------------------------
 */

export function useGenerateReport(
  onGenerated?: (
    report: Report,
  ) => void,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      payload: CreateReportRequest,
    ) =>
      generateReport(payload),

    onSuccess: (report: Report) => {
      /*
       * Update the detail cache immediately.
       *
       * This means the report page does not have to wait
       * for a second GET request just to display the generated
       * response.
       */
      queryClient.setQueryData(
        reportKeys.detail(report.id),
        report,
      );

      /*
       * Refresh report history so the new report appears
       * in the sidebar/list.
       */
      queryClient.invalidateQueries({
        queryKey: reportKeys.lists(),
      });

      /*
       * Allow the Reports page to automatically select
       * the newly generated report.
       *
       * Example:
       *
       * useGenerateReport((report) => {
       *   setSelectedReportId(report.id);
       * });
       */
      onGenerated?.(report);
    },
  });
}


/**
 * ---------------------------------------------------------------------------
 * UPDATE
 * ---------------------------------------------------------------------------
 */

export function useUpdateReport() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      reportId,
      payload,
    }: {
      reportId: number | string;
      payload: UpdateReportRequest;
    }) =>
      updateReport(
        reportId,
        payload,
      ),

    onSuccess: (report: Report) => {
      /*
       * Replace the detail cache with the
       * authoritative server response.
       */
      queryClient.setQueryData(
        reportKeys.detail(report.id),
        report,
      );

      /*
       * Refresh the report history because title,
       * status, summary, etc. may have changed.
       */
      queryClient.invalidateQueries({
        queryKey: reportKeys.lists(),
      });
    },
  });
}


/**
 * ---------------------------------------------------------------------------
 * DELETE
 * ---------------------------------------------------------------------------
 */

export function useDeleteReport() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      reportId: number | string,
    ) =>
      deleteReport(reportId),

    onSuccess: (_, reportId) => {
      /*
       * Remove the report from all cached detail data.
       */
      queryClient.removeQueries({
        queryKey:
          reportKeys.detail(reportId),
      });

      /*
       * Refresh report history.
       */
      queryClient.invalidateQueries({
        queryKey: reportKeys.lists(),
      });
    },
  });
}