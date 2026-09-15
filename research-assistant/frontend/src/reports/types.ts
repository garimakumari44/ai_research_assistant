/**
 * Report types used by the frontend report data layer.
 *
 * These types intentionally mirror the current FastAPI report API.
 */

/**
 * ---------------------------------------------------------------------------
 * REPORT STATUS
 * ---------------------------------------------------------------------------
 */

export type ReportStatus =
  | "draft"
  | "generating"
  | "completed"
  | "failed"
  | "archived";

/**
 * ---------------------------------------------------------------------------
 * EVIDENCE
 * ---------------------------------------------------------------------------
 */

export interface ReportEvidence {
  paper_id?: number | null;
  chunk_id?: number | null;

  citation_key?: string | null;

  title?: string | null;

  authors?: string[];

  year?: number | null;

  source?: string | null;

  quote?: string | null;

  evidence?: string | null;

  relevance_score?: number | null;
}

/**
 * ---------------------------------------------------------------------------
 * REPORT CONTENT
 * ---------------------------------------------------------------------------
 */

export interface ReportContent {
  executive_summary?: string | null;

  key_findings?: string[];

  methodology?: string | null;

  evidence_synthesis?: string | null;

  supporting_evidence?: Record<string, unknown>[];

  contradictions?: string[];

  research_gaps?: string[];

  emerging_trends?: string[];

  future_directions?: string[];

  conclusion?: string | null;

  references?: Record<string, unknown>[];
}

/**
 * ---------------------------------------------------------------------------
 * REPORT
 * ---------------------------------------------------------------------------
 */

export interface Report {
  id: number;

  user_id: number;

  title: string;

  research_question: string | null;

  status: ReportStatus;

  summary: string | null;

  content: ReportContent;

  evidence: ReportEvidence[];

  metadata: Record<string, unknown>;

  created_at: string;

  updated_at: string;

  completed_at: string | null;
}

/**
 * ---------------------------------------------------------------------------
 * REPORT LIST ITEM
 * ---------------------------------------------------------------------------
 */

export interface ReportListItem {
  id: number;

  title: string;

  research_question: string | null;

  status: ReportStatus;

  summary: string | null;

  created_at: string;

  updated_at: string;

  completed_at: string | null;
}

/**
 * ---------------------------------------------------------------------------
 * REPORT LIST RESPONSE
 * ---------------------------------------------------------------------------
 */

export interface ReportListResponse {
  items: ReportListItem[];

  total: number;

  page: number;

  page_size: number;

  pages: number;
}

/**
 * ---------------------------------------------------------------------------
 * REPORT LIST PARAMETERS
 * ---------------------------------------------------------------------------
 */

export interface ReportListParams {
  page?: number;

  page_size?: number;

  status?: ReportStatus;
}

/**
 * ---------------------------------------------------------------------------
 * CREATE REPORT REQUEST
 * ---------------------------------------------------------------------------
 */

export interface CreateReportRequest {
  title: string;

  research_question?: string | null;

  paper_ids?: number[];

  metadata?: Record<string, unknown>;
}

/**
 * ---------------------------------------------------------------------------
 * UPDATE REPORT REQUEST
 * ---------------------------------------------------------------------------
 */

export interface UpdateReportRequest {
  title?: string;

  research_question?: string | null;

  status?: ReportStatus;

  summary?: string | null;

  content?: ReportContent | null;

  evidence?: ReportEvidence[] | null;

  metadata?: Record<string, unknown> | null;
}