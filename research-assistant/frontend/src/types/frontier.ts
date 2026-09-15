/**
 * Research Frontier domain types.
 */

export type FrontierItemType =
  | "trend"
  | "gap"
  | "opportunity"
  | "emerging_topic"
  | "research_direction"
  | "open_problem";

export type TrendDirection =
  | "rising"
  | "stable"
  | "declining"
  | "emerging";

export interface FrontierItem {
  id: string;

  type: FrontierItemType;

  title: string;
  description: string;

  score?: number | null;

  confidence?: number | null;

  importance?: number | null;

  novelty_score?: number | null;

  evidence_count?: number | null;

  paper_count?: number | null;

  topic_ids?: string[];

  related_paper_ids?: string[];

  metadata?: Record<string, unknown>;

  created_at?: string | null;
  updated_at?: string | null;
}

export interface FrontierTrend {
  id: string;

  topic_id?: string | null;
  topic_name: string;

  direction: TrendDirection;

  growth_rate?: number | null;

  momentum_score?: number | null;

  publication_count?: number | null;

  citation_growth?: number | null;

  confidence?: number | null;

  time_series?: FrontierTimePoint[];

  related_topics?: string[];

  metadata?: Record<string, unknown>;
}

export interface FrontierTimePoint {
  date: string;

  value: number;

  count?: number;
}

export interface ResearchGap {
  id: string;

  title: string;
  description: string;

  gap_type?:
    | "knowledge"
    | "methodological"
    | "dataset"
    | "evaluation"
    | "theoretical"
    | "empirical"
    | "replication";

  severity?: number | null;

  confidence?: number | null;

  novelty_potential?: number | null;

  evidence_count?: number | null;

  supporting_paper_ids?: string[];

  related_topic_ids?: string[];

  metadata?: Record<string, unknown>;
}

export interface ResearchOpportunity {
  id: string;

  title: string;
  description: string;

  opportunity_score?: number | null;

  novelty_score?: number | null;

  feasibility_score?: number | null;

  impact_score?: number | null;

  related_gaps?: string[];
  related_trends?: string[];
  related_topics?: string[];

  suggested_methods?: string[];

  metadata?: Record<string, unknown>;
}

export interface NoveltyAnalysis {
  score: number;

  confidence?: number | null;

  novelty_level?:
    | "low"
    | "moderate"
    | "high"
    | "very_high";

  explanation?: string;

  novel_concepts?: string[];

  related_work?: string[];

  supporting_evidence?: string[];

  metadata?: Record<string, unknown>;
}

export interface FrontierOverview {
  total_items?: number;

  trends: FrontierTrend[];

  gaps: ResearchGap[];

  opportunities: ResearchOpportunity[];

  emerging_topics?: FrontierItem[];

  overall_novelty_score?: number | null;

  generated_at?: string | null;
}

export interface FrontierRequest {
  topic?: string;

  query?: string;

  collection_id?: string;

  paper_ids?: string[];

  limit?: number;

  min_confidence?: number;
}

export interface FrontierResponse {
  overview: FrontierOverview;

  items?: FrontierItem[];

  execution_time_ms?: number | null;
}