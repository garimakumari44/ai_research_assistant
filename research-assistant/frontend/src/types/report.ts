/**
 * Research report domain types.
 */

export type ReportStatus =
  | "draft"
  | "generating"
  | "completed"
  | "failed"
  | "archived";

export type ReportSectionType =
  | "title"
  | "abstract"
  | "introduction"
  | "background"
  | "literature_review"
  | "methodology"
  | "results"
  | "discussion"
  | "comparison"
  | "research_gaps"
  | "future_work"
  | "conclusion"
  | "references"
  | "custom";

export interface ReportCitation {
  id: string;

  paper_id?: string | null;

  document_id?: string | null;

  chunk_id?: string | null;

  citation_key?: string | null;

  text?: string | null;

  source_title?: string | null;

  authors?: string[];

  year?: number | null;

  url?: string | null;

  metadata?: Record<string, unknown>;
}

export interface ReportSection {
  id: string;

  report_id: string;

  type: ReportSectionType;

  title: string;

  content: string;

  order: number;

  citations?: ReportCitation[];

  metadata?: Record<string, unknown>;

  created_at?: string | null;
  updated_at?: string | null;
}

export interface Report {
  id: string;

  title: string;

  description?: string | null;

  status: ReportStatus;

  query?: string | null;

  collection_id?: string | null;

  sections?: ReportSection[];

  citation_count?: number;

  word_count?: number;

  page_count?: number;

  generation_time_ms?: number | null;

  created_at: string;
  updated_at: string;

  completed_at?: string | null;

  metadata?: Record<string, unknown>;
}

export interface ReportCreateRequest {
  title: string;

  description?: string;

  query: string;

  collection_id?: string;

  section_types?: ReportSectionType[];

  metadata?: Record<string, unknown>;
}

export interface ReportUpdateRequest {
  title?: string;

  description?: string;

  status?: ReportStatus;

  metadata?: Record<string, unknown>;
}

export interface ReportGenerationRequest {
  query: string;

  collection_id?: string;

  report_id?: string;

  sections?: ReportSectionType[];

  max_words?: number;

  include_citations?: boolean;

  include_research_gaps?: boolean;

  include_frontier_analysis?: boolean;

  include_graph_analysis?: boolean;
}

export interface ReportGenerationProgress {
  report_id: string;

  status: ReportStatus;

  progress: number;

  current_stage?: string | null;

  current_section?: string | null;

  completed_sections?: number;

  total_sections?: number;

  error?: string | null;
}

export interface ReportListResponse {
  reports: Report[];

  total: number;

  page?: number;
  page_size?: number;
}

export interface ReportResponse {
  report: Report;
}

export interface ReportDetailResponse {
  report: Report;

  sections: ReportSection[];

  citations?: ReportCitation[];
}