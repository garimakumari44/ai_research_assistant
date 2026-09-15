/**
 * Research domain types.
 *
 * Canonical shared types exchanged between the Next.js frontend
 * and the FastAPI research backend.
 *
 * Primary endpoint:
 *
 * POST /api/v1/research
 *
 * The request/response contracts in this file mirror the backend
 * Pydantic research models.
 */

/* -------------------------------------------------------------------------- */
/* Research status                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Lifecycle status used by research executions/sessions.
 */
export type ResearchStatus =
  | "pending"
  | "queued"
  | "planning"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

/**
 * Final status of a generated research report.
 */
export type ResearchReportStatus =
  | "completed"
  | "partial"
  | "failed";


/* -------------------------------------------------------------------------- */
/* Research depth                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Research depth accepted by the backend ResearchQuery model.
 */
export type ResearchDepth =
  | "basic"
  | "medium"
  | "deep";


/* -------------------------------------------------------------------------- */
/* Research strategy                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Strategy selected by the research planner/executor.
 *
 * `string` is retained for forward compatibility.
 */
export type ResearchStrategy =
  | "direct"
  | "rag"
  | "graph"
  | "corrective"
  | "hybrid"
  | "deep_research"
  | string;


/* -------------------------------------------------------------------------- */
/* Research request                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Canonical request payload sent to:
 *
 * POST /api/v1/research
 *
 * IMPORTANT:
 *
 * The backend expects the research question in the `question` field.
 *
 * Do NOT use `query` here.
 *
 * `query` is retained in execution/history types below because those
 * APIs may expose the original query under that name.
 */
export interface ResearchRequest {
  /**
   * Research question from the user.
   *
   * Backend validation:
   * - minimum length: 3
   * - maximum length: 5000
   */
  question: string;

  /**
   * Research depth.
   *
   * Backend default: "medium"
   */
  depth?: ResearchDepth;

  /**
   * Whether academic papers should be searched.
   *
   * Backend default: true.
   */
  include_papers?: boolean;

  /**
   * Whether GitHub implementations should be searched.
   *
   * Backend default: true.
   */
  include_github?: boolean;

  /**
   * Whether official documentation should be searched.
   *
   * Backend default: true.
   */
  include_docs?: boolean;
}


/**
 * Request/query type used by the research hook.
 *
 * This is intentionally an alias of ResearchRequest so the UI,
 * hook, and API client all use the same request contract.
 */
export type ResearchQuery = ResearchRequest;


/* -------------------------------------------------------------------------- */
/* Research plan                                                              */
/* -------------------------------------------------------------------------- */

/**
 * Represents the plan generated before research execution.
 *
 * This type is used by execution/history APIs and is not part of the
 * direct POST /api/v1/research request.
 */
export interface ResearchPlan {
  /**
   * Original research query.
   */
  query?: string;

  /**
   * Research objective.
   */
  objective?: string;

  /**
   * Selected research strategy.
   */
  strategy?: ResearchStrategy;

  /**
   * Research depth.
   */
  depth?: ResearchDepth;

  /**
   * Generated research steps.
   */
  steps?: ResearchPlanStep[];

  /**
   * Planned sources.
   */
  sources?: string[];

  /**
   * Expected outputs.
   */
  expected_outputs?: string[];

  /**
   * Additional metadata.
   */
  metadata?: Record<string, unknown>;
}


/**
 * Individual research plan step.
 */
export interface ResearchPlanStep {
  id?: string;

  order?: number;

  title?: string;

  description?: string;

  action?: string;

  strategy?: ResearchStrategy;

  status?: ResearchStatus;

  metadata?: Record<string, unknown>;
}


/* -------------------------------------------------------------------------- */
/* Research source                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Represents an information source used by the research pipeline.
 */
export interface ResearchSource {
  /**
   * Unique source identifier.
   */
  id: string;

  /**
   * Source title.
   */
  title: string;

  /**
   * Type of source.
   */
  source_type:
    | "paper"
    | "github"
    | "documentation"
    | "web"
    | "other";

  /**
   * Source URL.
   */
  url?: string | null;

  /**
   * Source authors.
   */
  authors: string[];

  /**
   * Extracted source content.
   */
  content: string;

  /**
   * Additional source metadata.
   */
  metadata: Record<string, unknown>;
}


/* -------------------------------------------------------------------------- */
/* Retrieved document                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Document or chunk returned by the retrieval pipeline.
 */
export interface RetrievedDocument {
  /**
   * Unique retrieved document ID.
   */
  id: string;

  /**
   * Source associated with this document.
   */
  source: ResearchSource;

  /**
   * Retrieved text.
   */
  text: string;

  /**
   * Retrieval relevance score.
   */
  score: number;

  /**
   * Optional chunk identifier.
   */
  chunk_id?: string | null;
}


/* -------------------------------------------------------------------------- */
/* Research claim                                                             */
/* -------------------------------------------------------------------------- */

/**
 * A claim generated or extracted during research.
 *
 * Primarily used by research execution/result pipelines.
 */
export interface ResearchClaim {
  /**
   * Unique claim identifier.
   */
  id: string;

  /**
   * Primary claim text.
   */
  claim: string;

  /**
   * Optional alternative statement representation.
   */
  statement?: string;

  /**
   * Claim confidence.
   */
  confidence?: number;

  /**
   * Claim relevance score.
   */
  relevance_score?: number;

  /**
   * Evidence supporting the claim.
   */
  evidence_ids?: string[];

  /**
   * Sources supporting the claim.
   */
  source_ids?: string[];

  /**
   * Citation identifiers associated with the claim.
   */
  citations?: string[];

  /**
   * Whether the claim is considered supported.
   */
  supported?: boolean;

  /**
   * Additional claim metadata.
   */
  metadata?: Record<string, unknown>;
}


/* -------------------------------------------------------------------------- */
/* Evidence                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Verified evidence supporting a research claim.
 */
export interface Evidence {
  /**
   * Unique evidence identifier.
   */
  id: string;

  /**
   * Claim supported by this evidence.
   */
  claim: string;

  /**
   * Original supporting evidence text.
   */
  supporting_text: string;

  /**
   * Source supporting this evidence.
   */
  source_id: string;

  /**
   * Evidence confidence score.
   *
   * Backend range: 0 to 1.
   */
  confidence: number;

  /**
   * Evidence relevance score.
   */
  relevance_score: number;
}


/**
 * Backwards-compatible alias.
 */
export type ResearchEvidence = Evidence;


/* -------------------------------------------------------------------------- */
/* Citation                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Generated citation reference.
 */
export interface Citation {
  /**
   * Unique citation identifier.
   */
  id: string;

  /**
   * Source identifier.
   */
  source_id: string;

  /**
   * Cited source title.
   */
  title: string;

  /**
   * Source authors.
   */
  authors: string[];

  /**
   * Publication year.
   */
  year?: number | null;

  /**
   * Human-readable citation.
   */
  citation_text: string;

  /**
   * Source URL.
   */
  url?: string | null;
}


/**
 * Backwards-compatible alias.
 */
export type ResearchCitation = Citation;


/* -------------------------------------------------------------------------- */
/* Comparison result                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Structured comparison result.
 */
export interface ComparisonResult {
  /**
   * Topic being compared.
   */
  topic: string;

  /**
   * Comparison criteria.
   */
  criteria: string[];

  /**
   * Comparison rows.
   */
  comparison_table: Record<string, string>[];
}


/* -------------------------------------------------------------------------- */
/* Research section                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Individual section of the generated research report.
 */
export interface ResearchSection {
  /**
   * Section title.
   */
  title: string;

  /**
   * Generated section content.
   */
  content: string;

  /**
   * Evidence IDs supporting this section.
   */
  evidence_ids: string[];
}


/* -------------------------------------------------------------------------- */
/* Research report                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Final generated research report.
 *
 * Backend endpoint:
 *
 * POST /api/v1/research
 */
export interface ResearchReport {
  /**
   * Research report title.
   */
  title: string;

  /**
   * Executive summary.
   */
  summary: string;

  /**
   * Generated research sections.
   */
  sections: ResearchSection[];

  /**
   * Citations used by the report.
   */
  citations: Citation[];

  /**
   * Supporting evidence.
   */
  evidence: Evidence[];

  /**
   * Sources used during research.
   */
  sources: ResearchSource[];

  /**
   * Structured comparison when applicable.
   */
  comparison?: ComparisonResult | null;

  /**
   * Pipeline and execution metadata.
   */
  metadata?: Record<string, unknown>;

  /**
   * Final report generation status.
   */
  status?: ResearchReportStatus;
}


/* -------------------------------------------------------------------------- */
/* Research response                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Current backend response for:
 *
 * POST /api/v1/research
 *
 * The endpoint returns a ResearchReport directly.
 */
export type ResearchResponse = ResearchReport;


/* -------------------------------------------------------------------------- */
/* Research result                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Research result stored inside the database or execution history.
 *
 * This is intentionally broader than ResearchReport because historical
 * execution records may contain intermediate or legacy result structures.
 */
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


/* -------------------------------------------------------------------------- */
/* Research execution                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Represents one research execution.
 *
 * Used by execution/history APIs.
 */
export interface ResearchExecution {
  /**
   * Unique execution identifier.
   */
  id: string;

  /**
   * Execution lifecycle status.
   */
  status: ResearchStatus;

  /**
   * Original research query.
   *
   * This remains `query` because it represents the historical
   * execution record, not the POST request payload.
   */
  query?: string;

  /**
   * Company being researched, when applicable.
   */
  company?: string;

  /**
   * Ticker symbol, when applicable.
   */
  ticker?: string;

  /**
   * Industry, when applicable.
   */
  industry?: string;

  /**
   * Associated project identifier.
   */
  project_id?: string | null;

  /**
   * Associated research session identifier.
   */
  session_id?: string | null;

  /**
   * Execution progress.
   */
  progress?: number;

  /**
   * Current pipeline stage.
   */
  current_stage?: string | null;

  /**
   * Human-readable execution message.
   */
  message?: string | null;

  /**
   * Error description.
   */
  error?: string | null;

  /**
   * Alternate error message field retained for compatibility.
   */
  error_message?: string | null;

  /**
   * Creation timestamp.
   */
  created_at?: string;

  /**
   * Execution start timestamp.
   */
  started_at?: string | null;

  /**
   * Execution completion timestamp.
   */
  completed_at?: string | null;

  /**
   * Last update timestamp.
   */
  updated_at?: string;

  /**
   * Generated research plan.
   */
  plan?: ResearchPlan | null;

  /**
   * Strategy selected for this execution.
   */
  strategy?: ResearchStrategy | null;

  /**
   * Claims generated during execution.
   */
  claims?: ResearchClaim[];

  /**
   * Execution result.
   */
  result?: ResearchResult | ResearchReport | null;

  /**
   * Additional execution metadata.
   */
  metadata?: Record<string, unknown>;
}


/* -------------------------------------------------------------------------- */
/* Research execution list                                                    */
/* -------------------------------------------------------------------------- */

/**
 * Paginated research execution list.
 */
export interface ResearchExecutionList {
  /**
   * Research executions in the current page.
   */
  items: ResearchExecution[];

  /**
   * Total number of executions.
   */
  total: number;

  /**
   * Current page number.
   */
  page?: number;

  /**
   * Number of records per page.
   */
  page_size?: number;

  /**
   * Total number of pages.
   */
  pages?: number;
}


/* -------------------------------------------------------------------------- */
/* Research session                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Session-based research state.
 *
 * Used by session/execution APIs and retained separately from the
 * canonical POST /api/v1/research request/response contract.
 */
export interface ResearchSession {
  /**
   * Unique session identifier.
   */
  id: string;

  /**
   * Session lifecycle status.
   */
  status: ResearchStatus;

  /**
   * Research query associated with the session.
   */
  query?: string;

  /**
   * Company being researched, when applicable.
   */
  company?: string;

  /**
   * Ticker symbol, when applicable.
   */
  ticker?: string;

  /**
   * Industry, when applicable.
   */
  industry?: string;

  /**
   * Session creation timestamp.
   */
  created_at?: string;

  /**
   * Last update timestamp.
   */
  updated_at?: string;

  /**
   * Associated execution ID.
   */
  execution_id?: string | null;

  /**
   * Research plan.
   */
  plan?: ResearchPlan | null;

  /**
   * Selected research strategy.
   */
  strategy?: ResearchStrategy | null;

  /**
   * Additional session metadata.
   */
  metadata?: Record<string, unknown>;

  /**
   * Final report, when available.
   */
  report?: ResearchReport | null;
}


/* -------------------------------------------------------------------------- */
/* Research health                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Research service health information.
 */
export interface ResearchHealth {
  /**
   * Overall service health.
   */
  status:
    | "healthy"
    | "degraded"
    | "unhealthy"
    | string;

  /**
   * Service name.
   */
  service?: string;

  /**
   * Service version.
   */
  version?: string;

  /**
   * Health-check timestamp.
   */
  timestamp?: string;

  /**
   * Individual component health information.
   */
  components?: Record<
    string,
    {
      status?: string;
      message?: string;
      latency_ms?: number;
    }
  >;
}