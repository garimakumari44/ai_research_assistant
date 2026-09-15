/**
 * Self-improvement domain types.
 *
 * Represents trace collection, evaluation, feedback,
 * learning, strategy performance, and optimization.
 */

export type TraceStage =
  | "query"
  | "planning"
  | "retrieval"
  | "documents"
  | "evidence"
  | "generation"
  | "answer";

export type EvaluationStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export type FeedbackType =
  | "positive"
  | "negative"
  | "correction"
  | "rating"
  | "comment";

export type OptimizationStatus =
  | "proposed"
  | "testing"
  | "validated"
  | "deployed"
  | "rejected"
  | "rolled_back";

export interface TraceEvent {
  id: string;

  trace_id: string;

  stage: TraceStage;

  timestamp: string;

  duration_ms?: number | null;

  input?: unknown;

  output?: unknown;

  metadata?: Record<string, unknown>;

  error?: string | null;
}

export interface ResearchTrace {
  id: string;

  query: string;

  session_id?: string | null;

  user_id?: string | null;

  started_at: string;

  completed_at?: string | null;

  duration_ms?: number | null;

  status: "running" | "completed" | "failed";

  events: TraceEvent[];

  metadata?: Record<string, unknown>;
}

export interface EvaluationMetric {
  name: string;

  value: number;

  score?: number | null;

  threshold?: number | null;

  passed?: boolean;

  explanation?: string | null;

  metadata?: Record<string, unknown>;
}

export interface EvaluationResult {
  id: string;

  trace_id: string;

  status: EvaluationStatus;

  overall_score?: number | null;

  metrics: EvaluationMetric[];

  strengths?: string[];

  weaknesses?: string[];

  recommendations?: string[];

  evaluator?: string | null;

  created_at: string;

  completed_at?: string | null;
}

export interface Feedback {
  id: string;

  trace_id?: string | null;

  evaluation_id?: string | null;

  type: FeedbackType;

  rating?: number | null;

  comment?: string | null;

  correction?: string | null;

  source?: "user" | "system" | "evaluation";

  created_at: string;

  metadata?: Record<string, unknown>;
}

export interface StrategyPerformance {
  strategy_id: string;

  strategy_name: string;

  strategy_type?: string | null;

  executions: number;

  successful_executions?: number;

  failed_executions?: number;

  average_score?: number | null;

  average_latency_ms?: number | null;

  average_cost?: number | null;

  success_rate?: number | null;

  improvement_rate?: number | null;

  trend?:
    | "improving"
    | "stable"
    | "declining";

  metadata?: Record<string, unknown>;
}

export interface LearningEvent {
  id: string;

  trace_id?: string | null;

  strategy_id?: string | null;

  type:
    | "pattern"
    | "correction"
    | "reward"
    | "penalty"
    | "strategy_update"
    | "knowledge_update";

  description: string;

  signal?: number | null;

  confidence?: number | null;

  created_at: string;

  metadata?: Record<string, unknown>;
}

export interface OptimizationProposal {
  id: string;

  title: string;

  description: string;

  target:
    | "retrieval"
    | "ranking"
    | "planning"
    | "generation"
    | "evidence"
    | "workflow"
    | "system";

  current_strategy?: string | null;

  proposed_strategy?: string | null;

  expected_improvement?: number | null;

  confidence?: number | null;

  status: OptimizationStatus;

  created_at: string;

  updated_at?: string | null;

  metadata?: Record<string, unknown>;
}

export interface SelfImprovementOverview {
  total_traces?: number;

  evaluated_traces?: number;

  average_score?: number | null;

  improvement_rate?: number | null;

  feedback_count?: number;

  learning_events?: number;

  active_optimizations?: number;

  strategy_performance: StrategyPerformance[];

  recent_evaluations?: EvaluationResult[];

  recent_feedback?: Feedback[];

  recent_optimizations?: OptimizationProposal[];
}

export interface TraceListResponse {
  traces: ResearchTrace[];

  total: number;

  page?: number;
  page_size?: number;
}

export interface TraceResponse {
  trace: ResearchTrace;

  evaluation?: EvaluationResult | null;

  feedback?: Feedback[];

  learning_events?: LearningEvent[];
}

export interface EvaluationListResponse {
  evaluations: EvaluationResult[];

  total: number;

  page?: number;
  page_size?: number;
}

export interface FeedbackCreateRequest {
  trace_id?: string;

  evaluation_id?: string;

  type: FeedbackType;

  rating?: number;

  comment?: string;

  correction?: string;
}

export interface OptimizationListResponse {
  optimizations: OptimizationProposal[];

  total: number;
}

export interface SelfImprovementResponse {
  overview: SelfImprovementOverview;
}