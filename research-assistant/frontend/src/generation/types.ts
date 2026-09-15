/**
 * Generation layer types.
 *
 * Generation is the final synthesis layer of the research pipeline.
 *
 * Research context can originate from:
 * - retrieval
 * - knowledge graph
 * - citations
 * - verification
 * - research planning
 */

/* -------------------------------------------------------------------------- */
/* Enums / unions                                                             */
/* -------------------------------------------------------------------------- */

export type GenerationMode =
  | "answer"
  | "summary"
  | "research"
  | "synthesis"
  | "extraction";

export type GenerationStatus =
  | "idle"
  | "queued"
  | "running"
  | "completed"
  | "failed";

export type CitationType =
  | "document"
  | "page"
  | "section"
  | "web"
  | "graph"
  | "unknown";

export type VerificationStatus =
  | "verified"
  | "partially_verified"
  | "unverified"
  | "failed";

export type GenerationEvidenceType =
  | "retrieval"
  | "graph"
  | "citation"
  | "verification"
  | "research_plan";

/* -------------------------------------------------------------------------- */
/* Request                                                                    */
/* -------------------------------------------------------------------------- */

export interface GenerationOptions {
  temperature?: number;

  max_tokens?: number;

  include_citations?: boolean;

  verify?: boolean;

  system_prompt?: string;

  model?: string;

  num_candidates?: number;
}

export interface GenerationRequest {
  /**
   * User's research question or instruction.
   */
  query: string;

  /**
   * Evidence returned by the retrieval layer.
   */
  retrieved_evidence?: RetrievedEvidence[];

  /**
   * Evidence originating from the knowledge graph.
   */
  graph_evidence?: GraphEvidence[];

  /**
   * Source citations available to generation.
   */
  citations?: GenerationCitation[];

  /**
   * Verification results produced before generation.
   */
  verification?: GenerationVerification;

  /**
   * Research plan guiding synthesis.
   */
  research_plan?: ResearchPlan;

  /**
   * Optional legacy/general generation context.
   *
   * Kept for compatibility with existing callers.
   */
  context?: GenerationContext[];

  /**
   * Generation mode.
   */
  mode?: GenerationMode;

  /**
   * Adaptive RAG execution ID.
   */
  rag_execution_id?: string;

  /**
   * Research execution/session ID.
   */
  research_execution_id?: string;

  /**
   * Conversation ID.
   */
  conversation_id?: string;

  options?: GenerationOptions;
}

/* -------------------------------------------------------------------------- */
/* Retrieved evidence                                                         */
/* -------------------------------------------------------------------------- */

export interface RetrievedEvidence {
  id: string;

  content: string;

  document_id?: string;

  document_title?: string;

  chunk_id?: string;

  page_number?: number;

  section?: string;

  score?: number;

  retrieval_method?:
    | "semantic"
    | "keyword"
    | "hybrid"
    | "reranked"
    | "unknown";

  rank?: number;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Graph evidence                                                             */
/* -------------------------------------------------------------------------- */

export type GraphEvidenceType =
  | "entity"
  | "relationship"
  | "path"
  | "subgraph"
  | "claim";

export interface GraphEvidence {
  id: string;

  type: GraphEvidenceType;

  /**
   * Human-readable graph evidence.
   */
  content: string;

  entity_ids?: string[];

  relationship_ids?: string[];

  source_ids?: string[];

  path?: string[];

  confidence?: number;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Research plan                                                              */
/* -------------------------------------------------------------------------- */

export type ResearchPlanStepType =
  | "retrieval"
  | "graph"
  | "verification"
  | "comparison"
  | "synthesis"
  | "report";

export interface ResearchPlanStep {
  id: string;

  title: string;

  description?: string;

  type: ResearchPlanStepType;

  order: number;

  status?: "pending" | "running" | "completed" | "failed";

  query?: string;

  evidence_ids?: string[];

  metadata?: Record<string, unknown>;
}

export interface ResearchPlan {
  id: string;

  objective: string;

  steps: ResearchPlanStep[];

  /**
   * Research questions/subquestions produced by planning.
   */
  questions?: string[];

  /**
   * Expected synthesis direction.
   */
  synthesis_goal?: string;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* General context                                                            */
/* -------------------------------------------------------------------------- */

export interface GenerationContext {
  id: string;

  content: string;

  document_id?: string;

  document_title?: string;

  page_number?: number;

  section?: string;

  score?: number;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Citations                                                                  */
/* -------------------------------------------------------------------------- */

export interface GenerationCitation {
  id: string;

  type: CitationType;

  marker?: string;

  title?: string;

  document_id?: string;

  document_title?: string;

  page_number?: number;

  section?: string;

  source_url?: string;

  excerpt?: string;

  confidence?: number;

  /**
   * IDs of evidence items supporting this citation.
   */
  evidence_ids?: string[];
}

/* -------------------------------------------------------------------------- */
/* Verification                                                               */
/* -------------------------------------------------------------------------- */

export interface VerificationClaim {
  id: string;

  claim: string;

  supported: boolean;

  confidence: number;

  citation_ids?: string[];

  evidence_ids?: string[];

  explanation?: string;
}

export interface GenerationVerification {
  status: VerificationStatus;

  confidence: number;

  claims: VerificationClaim[];

  issues?: string[];

  summary?: string;

  /**
   * Number of claims evaluated.
   */
  claim_count?: number;

  /**
   * Number of claims supported by evidence.
   */
  supported_claim_count?: number;
}

/* -------------------------------------------------------------------------- */
/* Generation trace                                                           */
/* -------------------------------------------------------------------------- */

export type GenerationTraceEventType =
  | "planning"
  | "prompt"
  | "retrieval"
  | "graph"
  | "citation"
  | "verification"
  | "synthesis"
  | "model"
  | "completion"
  | "error";

export interface GenerationTraceEvent {
  id: string;

  type: GenerationTraceEventType;

  message: string;

  timestamp: string;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Usage                                                                      */
/* -------------------------------------------------------------------------- */

export interface GenerationUsage {
  prompt_tokens?: number;

  completion_tokens?: number;

  total_tokens?: number;

  latency_ms?: number;
}

/* -------------------------------------------------------------------------- */
/* Response                                                                   */
/* -------------------------------------------------------------------------- */

export interface GenerationResponse {
  id: string;

  status: GenerationStatus;

  answer: string;

  title?: string;

  mode?: GenerationMode;

  model?: string;

  citations: GenerationCitation[];

  verification?: GenerationVerification;

  trace?: GenerationTraceEvent[];

  usage?: GenerationUsage;

  confidence?: number;

  /**
   * Research context actually used by generation.
   */
  evidence_used?: {
    retrieved: string[];
    graph: string[];
    citations: string[];
    verification_claims: string[];
  };

  error?: string;

  created_at?: string;

  completed_at?: string;
}

/* -------------------------------------------------------------------------- */
/* Streaming                                                                  */
/* -------------------------------------------------------------------------- */

export interface GenerationStreamChunk {
  id: string;

  type:
    | "start"
    | "token"
    | "citation"
    | "verification"
    | "trace"
    | "complete"
    | "error";

  content?: string;

  citation?: GenerationCitation;

  verification?: GenerationVerification;

  trace?: GenerationTraceEvent;

  response?: GenerationResponse;

  error?: string;
}

/* -------------------------------------------------------------------------- */
/* Execution                                                                   */
/* -------------------------------------------------------------------------- */

export interface GenerationHealth {
  status: "healthy" | "degraded" | "unhealthy";

  provider?: string;

  model?: string;

  message?: string;
}

export interface GenerationExecution {
  id: string;

  query: string;

  status: GenerationStatus;

  created_at: string;

  completed_at?: string;

  response?: GenerationResponse;

  error?: string;
}

export interface GenerationExecutionList {
  items: GenerationExecution[];

  total: number;

  page?: number;

  page_size?: number;
}