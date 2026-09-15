/**
 * Canonical research domain types.
 *
 * Shared between the research API, research execution/history,
 * evidence UI, citations, planning UI, verification UI,
 * and report UI.
 */

export type ResearchStatus =
  | "idle"
  | "pending"
  | "queued"
  | "planning"
  | "searching"
  | "retrieving"
  | "running"
  | "synthesizing"
  | "verifying"
  | "completed"
  | "failed"
  | "cancelled";

export type ResearchReportStatus =
  | "completed"
  | "partial"
  | "failed";

export type ResearchDepth =
  | "basic"
  | "medium"
  | "deep";

export type ResearchStrategy =
  | "direct"
  | "rag"
  | "graph"
  | "corrective"
  | "hybrid"
  | "deep_research"
  | string;

export type EvidenceSourceType =
  | "semantic"
  | "keyword"
  | "graph"
  | "paper"
  | "web"
  | "github"
  | "documentation"
  | "document"
  | "database"
  | "other";

export type ResearchTaskStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped"
  | "passed"
  | "verified"
  | "partial";

export interface ResearchRequest {
  question: string;
  depth?: ResearchDepth;
  include_papers?: boolean;
  include_github?: boolean;
  include_docs?: boolean;
}

export type ResearchQuery = ResearchRequest;

export interface ResearchPlanStep {
  id?: string;
  order?: number;
  title?: string;
  description?: string;
  action?: string;
  strategy?: ResearchStrategy;

  /**
   * Execution status can be broader than task status because
   * plan steps participate in the research lifecycle.
   */
  status?: ResearchStatus;

  metadata?: Record<string, unknown>;
}

export interface ResearchPlan {
  query?: string;
  objective?: string;
  strategy?: ResearchStrategy;
  depth?: ResearchDepth;

  steps?: ResearchPlanStep[];

  sources?: string[];
  expected_outputs?: string[];

  metadata?: Record<string, unknown>;
}

export interface ResearchSource {
  id: string;
  title: string;

  source_type:
    | "paper"
    | "github"
    | "documentation"
    | "web"
    | "document"
    | "database"
    | "other";

  url?: string | null;

  authors: string[];

  author?: string | null;
  domain?: string | null;

  content: string;

  metadata: Record<string, unknown>;
}

export interface RetrievedDocument {
  id: string;
  source: ResearchSource;
  text: string;
  score: number;
  chunk_id?: string | null;
}

export interface ResearchClaim {
  id: string;
  claim: string;
  statement?: string;

  confidence?: number;
  relevance_score?: number;

  evidence_ids?: string[];
  source_ids?: string[];
  citations?: string[];

  supported?: boolean;

  metadata?: Record<string, unknown>;
}

export interface Evidence {
  id: string;

  claim: string;
  supporting_text: string;
  source_id: string;

  confidence: number;
  relevance_score: number;

  sourceType?: EvidenceSourceType;
  score?: number;

  title?: string;
  content?: string;
  relation?: string;

  paperId?: number | string | null;
  documentId?: number | string | null;

  page?: number | null;
  sectionId?: string | number | null;
}

export type ResearchEvidence = Evidence;

export interface Citation {
  id: string;
  source_id: string;

  title: string;
  authors: string[];

  year?: number | null;

  citation_text: string;

  url?: string | null;

  venue?: string | null;

  evidenceIds?: string[];

  sourceUrl?: string | null;
}

export type ResearchCitation = Citation;

export interface ComparisonResult {
  topic: string;
  criteria: string[];
  comparison_table: Record<string, string>[];
}

export interface ResearchSection {
  title: string;
  content: string;
  evidence_ids: string[];
}

export interface ResearchAnswer {
  title?: string;

  summary?: string;

  answer?: string;

  content?: string;

  /**
   * Confidence of the synthesized answer.
   * Usually represented as 0..1.
   */
  confidence?: number;

  evidence?: Evidence[];

  citations?: Citation[];

  verification?: VerificationSummary;

  sections?: ResearchSection[];
}

export interface ResearchReport {
  title: string;
  summary: string;

  sections: ResearchSection[];

  citations: Citation[];

  evidence: Evidence[];

  sources: ResearchSource[];

  comparison?: ComparisonResult | null;

  metadata?: Record<string, unknown>;

  status?: ResearchReportStatus;
}

export type ResearchResponse = ResearchReport;

export interface ResearchResult {
  summary?: string;
  answer?: string;
  thesis?: string;
  recommendation?: string;

  confidence?: number;

  sections?: ResearchSection[];

  evidence?: Evidence[];

  claims?: ResearchClaim[];

  report?: ResearchReport | null;

  data?: Record<string, unknown>;
}

export interface ResearchTask {
  id: string;

  title?: string;
  description?: string;

  /**
   * Query executed by this research task.
   */
  query?: string;

  status: ResearchTaskStatus;

  progress?: number;

  strategy?: ResearchStrategy;

  /**
   * Task output/result.
   */
  result?: unknown;

  /**
   * Number of retrieved/search results produced by the task.
   */
  resultCount?: number;

  /**
   * Task execution duration in milliseconds.
   */
  durationMs?: number;

  error?: string | null;

  started_at?: string | null;
  completed_at?: string | null;

  metadata?: Record<string, unknown>;
}

export interface VerificationCheck {
  id?: string;

  name?: string;
  label?: string;

  /**
   * Claim being verified.
   */
  claim?: string;

  /**
   * Human-readable explanation of the verification result.
   */
  explanation?: string;

  status?:
    | ResearchTaskStatus
    | "verified"
    | "partial"
    | "passed"
    | "failed";

  passed?: boolean;

  confidence?: number;

  score?: number;

  message?: string;

  details?: string;
}

export interface VerificationSummary {
  /**
   * Overall verification state.
   */
  status?:
    | "verified"
    | "partial"
    | "failed"
    | string;

  verified?: boolean;

  confidence?: number;

  score?: number;

  verifiedClaims?: number;

  totalClaims?: number;

  total?: number;

  passed?: number;

  failed?: number;

  /**
   * Normalized to an array by consumers when necessary.
   */
  checks?: VerificationCheck[];

  notes?: string[];
}

export interface ResearchExecution {
  id: string;

  status: ResearchStatus;

  query?: string;

  company?: string;
  ticker?: string;
  industry?: string;

  project_id?: string | null;
  session_id?: string | null;

  progress?: number;

  current_stage?: string | null;

  message?: string | null;

  error?: string | null;
  error_message?: string | null;

  created_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
  updated_at?: string;

  plan?: ResearchPlan | null;

  strategy?: ResearchStrategy | null;

  claims?: ResearchClaim[];

  answer?: ResearchAnswer | null;

  result?: ResearchResult | ResearchReport | null;

  metadata?: Record<string, unknown>;
}

export interface ResearchExecutionList {
  items: ResearchExecution[];

  total: number;

  page?: number;
  page_size?: number;
  pages?: number;
}

export interface ResearchSession {
  id: string;

  status: ResearchStatus;

  query?: string;

  company?: string;
  ticker?: string;
  industry?: string;

  created_at?: string;
  updated_at?: string;

  execution_id?: string | null;

  plan?: ResearchPlan | null;

  strategy?: ResearchStrategy | null;

  retrievalModes?: string[];

  iterations?: number;

  durationMs?: number;

  tasks?: ResearchTask[];

  metadata?: Record<string, unknown>;

  report?: ResearchReport | null;
}

export interface ResearchHealth {
  status:
    | "healthy"
    | "degraded"
    | "unhealthy"
    | string;

  service?: string;

  version?: string;

  timestamp?: string;

  components?: Record<
    string,
    {
      status?: string;
      message?: string;
      latency_ms?: number;
    }
  >;
}