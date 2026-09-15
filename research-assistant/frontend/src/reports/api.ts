import {
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
} from "@/lib/api";

import type {
  CreateReportRequest,
  Report,
  ReportListParams,
  ReportListResponse,
  UpdateReportRequest,
} from "./types";

/**
 * ---------------------------------------------------------------------------
 * API ENDPOINT
 * ---------------------------------------------------------------------------
 *
 * All authentication is handled by the central API client.
 *
 * The central client is responsible for:
 * - attaching the access token
 * - detecting 401 responses
 * - refreshing the access token
 * - retrying the original request
 * - logging the user out when refresh fails
 *
 * Do NOT use fetch() directly in this file.
 * ---------------------------------------------------------------------------
 */

const REPORTS_ENDPOINT = "/reports";

/**
 * ---------------------------------------------------------------------------
 * QUERY PARAMETERS
 * ---------------------------------------------------------------------------
 */

function buildReportQuery(
  params?: ReportListParams,
): string {
  if (!params) {
    return "";
  }

  const searchParams = new URLSearchParams();

  if (params.page !== undefined) {
    searchParams.set(
      "page",
      String(params.page),
    );
  }

  if (params.page_size !== undefined) {
    searchParams.set(
      "page_size",
      String(params.page_size),
    );
  }

  if (params.status !== undefined) {
    searchParams.set(
      "status",
      params.status,
    );
  }

  const query = searchParams.toString();

  return query ? `?${query}` : "";
}

/**
 * ---------------------------------------------------------------------------
 * GET REPORTS
 * ---------------------------------------------------------------------------
 */

export async function getReports(
  params?: ReportListParams,
): Promise<ReportListResponse> {
  const query = buildReportQuery(params);

  return apiGet<ReportListResponse>(
    `${REPORTS_ENDPOINT}${query}`,
  );
}

/**
 * ---------------------------------------------------------------------------
 * GET SINGLE REPORT
 * ---------------------------------------------------------------------------
 */

export async function getReport(
  reportId: number | string,
): Promise<Report> {
  const normalizedId = String(reportId).trim();

  if (!normalizedId) {
    throw new Error("Report ID is required.");
  }

  return apiGet<Report>(
    `${REPORTS_ENDPOINT}/${encodeURIComponent(normalizedId)}`,
  );
}

/**
 * ---------------------------------------------------------------------------
 * CREATE REPORT
 * ---------------------------------------------------------------------------
 */

export async function createReport(
  payload: CreateReportRequest,
): Promise<Report> {
  if (!payload) {
    throw new Error(
      "Report payload is required.",
    );
  }

  return apiPost<Report>(
    REPORTS_ENDPOINT,
    payload,
  );
}

/**
 * ---------------------------------------------------------------------------
 * GENERATE REPORT
 * ---------------------------------------------------------------------------
 */

export async function generateReport(
  payload: CreateReportRequest,
): Promise<Report> {
  if (!payload) {
    throw new Error(
      "Report generation payload is required.",
    );
  }

  return apiPost<Report>(
    `${REPORTS_ENDPOINT}/generate`,
    payload,
  );
}

/**
 * ---------------------------------------------------------------------------
 * UPDATE REPORT
 * ---------------------------------------------------------------------------
 */

export async function updateReport(
  reportId: number | string,
  payload: UpdateReportRequest,
): Promise<Report> {
  const normalizedId = String(reportId).trim();

  if (!normalizedId) {
    throw new Error("Report ID is required.");
  }

  if (!payload) {
    throw new Error(
      "Report update payload is required.",
    );
  }

  return apiPatch<Report>(
    `${REPORTS_ENDPOINT}/${encodeURIComponent(normalizedId)}`,
    payload,
  );
}

/**
 * ---------------------------------------------------------------------------
 * DELETE REPORT
 * ---------------------------------------------------------------------------
 */

export async function deleteReport(
  reportId: number | string,
): Promise<void> {
  const normalizedId = String(reportId).trim();

  if (!normalizedId) {
    throw new Error("Report ID is required.");
  }

  await apiDelete<void>(
    `${REPORTS_ENDPOINT}/${encodeURIComponent(normalizedId)}`,
  );
}