/**
 * Adaptive RAG frontend types.
 *
 * Adaptive RAG is the orchestration layer between:
 *
 * Paper Foundation
 *      ↓
 * Documents
 *      ↓
 * Knowledge
 *      ↓
 * Retrieval
 *      ↓
 * Adaptive RAG
 *      ↓
 * Generation
 *      ↓
 * Research Engine
 *      ↓
 * Research Graph
 *      ↓
 * Research Frontier
 *      ↓
 * Self-Improvement
 *      ↓
 * Reports / Collections
 *
 * These types intentionally keep the frontend contract stable while
 * allowing individual backend services to evolve independently.
 */

/* -------------------------------------------------------------------------- */
/* Strategies                                                                 */
/* -------------------------------------------------------------------------- */

export type RAGStrategy =
  | "direct"
  | "dense"
  | "hybrid"
  | "multi_query"
  | "iterative"
  | "corrective"
  | "graph_augmented"
  | "auto";

export type RoutingDecision =
  | "direct"
  | "retrieve"
  | "refine"
  | "retry"
  | "graph"
  | "generate"
  | "research"
  | "stop";

export type RetrievalMode =
  | "vector"
  | "keyword"
  | "hybrid"
  | "graph";

export type ConfidenceLevel =
  | "low"
  | "medium"
  | "high";

export type ExecutionStatus =
  | "pending"
  | "planning"
  | "retrieving"
  | "generating"
  | "evaluating"
  | "researching"
  | "completed"
  | "failed"
  | "stopped";

/* -------------------------------------------------------------------------- */
/* Platform Layers                                                            */
/* -------------------------------------------------------------------------- */

export type PlatformLayer =
  | "papers"
  | "documents"
  | "knowledge"
  | "retrieval"
  | "adaptive_rag"
  | "generation"
  | "research"
  | "graph"
  | "frontier"
  | "self_improvement"
  | "reports"
  | "collections";

export interface LayerExecution {
  layer: PlatformLayer;

  status:
    | "pending"
    | "running"
    | "completed"
    | "skipped"
    | "failed";

  started_at?: string;
  completed_at?: string;

  duration_ms?: number;

  error?: string;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Strategy Metadata                                                          */
/* -------------------------------------------------------------------------- */

export interface StrategyOption {
  id: RAGStrategy;

  name: string;

  description: string;

  recommended?: boolean;

  enabled?: boolean;

  requires_graph?: boolean;

  requires_retrieval?: boolean;

  supports_multi_query?: boolean;

  supports_correction?: boolean;
}

/* -------------------------------------------------------------------------- */
/* Request                                                                    */
/* -------------------------------------------------------------------------- */

export interface AdaptiveRAGRequest {
  query: string;

  conversation_id?: string;

  execution_id?: string;

  /**
   * Research collection used as the primary scope.
   */
  collection_id?: string;

  /**
   * Optional explicit document scope.
   */
  document_ids?: string[];

  /**
   * Optional paper scope.
   */
  paper_ids?: string[];

  /**
   * Automatically choose the best strategy.
   */
  adaptive?: boolean;

  strategy?: RAGStrategy;

  max_iterations?: number;

  confidence_threshold?: number;

  top_k?: number;

  retrieval_mode?: RetrievalMode;

  /* ------------------------------ Graph ---------------------------------- */

  enable_graph?: boolean;

  graph_depth?: number;

  graph_node_types?: string[];

  graph_edge_types?: string[];

  /* --------------------------- Multi Query ------------------------------- */

  enable_multi_query?: boolean;

  max_query_variants?: number;

  /* ---------------------------- Correction ------------------------------- */

  enable_correction?: boolean;

  max_correction_attempts?: number;

  /* ---------------------------- Generation ------------------------------- */

  enable_generation?: boolean;

  generation_model?: string;

  temperature?: number;

  max_output_tokens?: number;

  /* ----------------------------- Research -------------------------------- */

  enable_research?: boolean;

  research_depth?: number;

  research_steps?: number;

  /* ----------------------------- Frontier ------------------------------- */

  enable_frontier?: boolean;

  analyze_gaps?: boolean;

  analyze_trends?: boolean;

  analyze_novelty?: boolean;

  /* ------------------------- Self Improvement ---------------------------- */

  enable_evaluation?: boolean;

  collect_feedback?: boolean;

  trace_execution?: boolean;

  /* ---------------------------- Output ----------------------------------- */

  generate_report?: boolean;

  save_to_collection?: boolean;

  target_collection_id?: string;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Retrieval                                                                  */
/* -------------------------------------------------------------------------- */

export interface RetrievedChunk {
  id: string;

  document_id?: string;

  document_name?: string;

  paper_id?: string;

  paper_title?: string;

  content: string;

  score?: number;

  rank?: number;

  source_type?: string;

  metadata?: Record<string, unknown>;
}

export interface RetrievalStep {
  step: number;

  query: string;

  mode: RetrievalMode;

  strategy?: RAGStrategy;

  chunks: RetrievedChunk[];

  result_count: number;

  duration_ms?: number;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Graph                                                                     */
/* -------------------------------------------------------------------------- */

export interface GraphNode {
  id: string;

  type: string;

  label?: string;

  score?: number;

  paper_id?: string;

  document_id?: string;

  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;

  source: string;

  target: string;

  type: string;

  weight?: number;

  metadata?: Record<string, unknown>;
}

export interface GraphContext {
  enabled: boolean;

  query?: string;

  depth?: number;

  nodes: GraphNode[];

  edges: GraphEdge[];

  seed_node_ids?: string[];

  traversal_path?: string[];

  result_count?: number;

  duration_ms?: number;
}

/* -------------------------------------------------------------------------- */
/* Frontier                                                                   */
/* -------------------------------------------------------------------------- */

export interface FrontierContext {
  enabled: boolean;

  trends?: string[];

  gaps?: string[];

  novelty_score?: number;

  emerging_topics?: string[];

  related_topics?: string[];

  duration_ms?: number;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Query Planning                                                             */
/* -------------------------------------------------------------------------- */

export interface QueryPlan {
  strategy: RAGStrategy;

  reasoning?: string;

  steps: string[];

  estimated_iterations?: number;

  retrieval_required: boolean;

  graph_required?: boolean;

  multi_query_required?: boolean;

  corrective_retrieval?: boolean;

  generation_required?: boolean;

  research_required?: boolean;

  frontier_analysis_required?: boolean;
}

/* -------------------------------------------------------------------------- */
/* Confidence / Evaluation                                                    */
/* -------------------------------------------------------------------------- */

export interface ConfidenceScore {
  score: number;

  level: ConfidenceLevel;

  threshold?: number;

  reasons?: string[];

  grounded?: boolean;
}

export interface EvaluationResult {
  confidence: ConfidenceScore;

  answerable: boolean;

  grounded: boolean;

  complete: boolean;

  relevant: boolean;

  should_continue: boolean;

  should_retrieve_again: boolean;

  should_use_graph?: boolean;

  should_research?: boolean;

  feedback?: string[];

  missing_information?: string[];

  hallucination_risk?: number;
}

/* -------------------------------------------------------------------------- */
/* Generation                                                                 */
/* -------------------------------------------------------------------------- */

export interface GenerationResult {
  answer: string;

  model?: string;

  provider?: string;

  finish_reason?: string;

  token_count?: number;

  citations?: string[];

  grounded?: boolean;

  duration_ms?: number;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Research                                                                   */
/* -------------------------------------------------------------------------- */

export interface ResearchStep {
  step: number;

  title?: string;

  query: string;

  status:
    | "pending"
    | "running"
    | "completed"
    | "failed";

  findings?: string[];

  source_ids?: string[];

  duration_ms?: number;
}

export interface ResearchContext {
  enabled: boolean;

  research_id?: string;

  depth?: number;

  steps: ResearchStep[];

  findings?: string[];

  conclusions?: string[];

  duration_ms?: number;
}


/* -------------------------------------------------------------------------- */
/* Trace                                                                      */
/* -------------------------------------------------------------------------- */

export type TraceStepStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export interface RAGTraceStep {
  id?: string;

  index: number;

  title?: string;

  name?: string;

  description?: string;

  type?: string;

  status?: TraceStepStatus;

  duration_ms?: number;

  started_at?: number;

  finished_at?: number;

  strategy?: string;

  error?: string;

  metadata?: Record<string, unknown>;
}

export interface AdaptiveRAGTrace {
  execution_id?: string;

  query?: string;

  status?: ExecutionStatus;

  steps: RAGTraceStep[];

  total_duration_ms?: number;

  metadata?: Record<string, unknown>;
}
/* -------------------------------------------------------------------------- */
/* Execution State                                                            */
/* -------------------------------------------------------------------------- */

export interface AdaptiveRAGState {
  execution_id: string;

  query: string;

  status: ExecutionStatus;

  iteration: number;

  max_iterations: number;

  strategy: RAGStrategy;

  routing_decision?: RoutingDecision;

  plan?: QueryPlan;

  layers?: LayerExecution[];

  retrieval_steps: RetrievalStep[];

  retrieved_chunks: RetrievedChunk[];

  graph?: GraphContext;

  frontier?: FrontierContext;

  research?: ResearchContext;

  generation?: GenerationResult;

  answer?: string;

  confidence?: ConfidenceScore;

  evaluation?: EvaluationResult;

  error?: string;

  started_at?: string;

  completed_at?: string;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Response                                                                   */
/* -------------------------------------------------------------------------- */

export interface AdaptiveRAGResponse {
  execution_id: string;

  status: ExecutionStatus;

  query: string;

  answer?: string;

  strategy: RAGStrategy;

  routing_decision?: RoutingDecision;

  state?: AdaptiveRAGState;

  plan?: QueryPlan;

  layers?: LayerExecution[];

  confidence?: ConfidenceScore;

  evaluation?: EvaluationResult;

  generation?: GenerationResult;

  graph?: GraphContext;

  frontier?: FrontierContext;

  research?: ResearchContext;

  sources: RetrievedChunk[];

  retrieval_steps?: RetrievalStep[];

  iterations: number;

  duration_ms?: number;

  error?: string;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Execution List                                                             */
/* -------------------------------------------------------------------------- */

export interface AdaptiveRAGExecution {
  execution_id: string;

  query: string;

  status: ExecutionStatus;

  strategy: RAGStrategy;

  iteration: number;

  confidence?: number;

  created_at?: string;

  completed_at?: string;

  layers?: LayerExecution[];
}

export interface AdaptiveRAGExecutionList {
  items: AdaptiveRAGExecution[];

  total: number;

  page?: number;

  page_size?: number;
}

/* -------------------------------------------------------------------------- */
/* Health                                                                     */
/* -------------------------------------------------------------------------- */

export interface AdaptiveRAGHealth {
  status:
    | "healthy"
    | "degraded"
    | "unhealthy";

  adaptive_rag_enabled: boolean;

  available_strategies: RAGStrategy[];

  available_layers?: PlatformLayer[];

  graph_enabled?: boolean;

  frontier_enabled?: boolean;

  research_enabled?: boolean;

  generation_enabled?: boolean;

  evaluation_enabled?: boolean;

  version?: string;
}

/* -------------------------------------------------------------------------- */
/* Configuration                                                              */
/* -------------------------------------------------------------------------- */

export interface AdaptiveRAGConfig {
  default_strategy: RAGStrategy;

  default_top_k: number;

  default_max_iterations: number;

  default_confidence_threshold: number;

  enabled_strategies: RAGStrategy[];

  enabled_retrieval_modes: RetrievalMode[];

  graph_enabled: boolean;

  frontier_enabled?: boolean;

  research_enabled?: boolean;

  generation_enabled?: boolean;

  evaluation_enabled?: boolean;

  corrective_retrieval_enabled: boolean;

  multi_query_enabled: boolean;

  available_layers?: PlatformLayer[];
}
