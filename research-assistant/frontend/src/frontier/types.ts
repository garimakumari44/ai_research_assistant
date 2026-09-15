/**
 * Research trend.
 */
export interface Trend {
  id: string;
  name: string;
  description?: string;

  score: number;
  growthRate?: number;

  direction:
    | "rising"
    | "stable"
    | "declining";

  paperCount?: number;

  period?: string;

  relatedTopics?: string[];

  metadata?: Record<string, unknown>;
}

/**
 * Research gap.
 */
export interface Gap {
  id: string;

  title: string;
  description: string;

  confidence: number;

  importance?: number;

  evidenceCount?: number;

  relatedTopics?: string[];

  supportingPapers?: string[];

  suggestedResearch?: string[];

  metadata?: Record<string, unknown>;
}

/**
 * Novelty analysis result.
 */
export interface NoveltyAnalysis {
  query: string;

  noveltyScore: number;

  originalityScore?: number;

  saturationScore?: number;

  confidence: number;

  classification:
    | "highly_novel"
    | "novel"
    | "moderately_novel"
    | "low_novelty"
    | "saturated";

  explanation?: string;

  relatedWork?: Array<{
    id: string;
    title: string;
    similarity: number;
  }>;

  novelDimensions?: string[];

  metadata?: Record<string, unknown>;
}

/**
 * Overall research frontier.
 */
export interface FrontierOverview {
  topic?: string;

  generatedAt?: string;

  trends: Trend[];

  gaps: Gap[];

  novelty?: NoveltyAnalysis;

  frontierScore?: number;

  emergingTopics?: string[];

  decliningTopics?: string[];

  metadata?: Record<string, unknown>;
}

/**
 * Common API error.
 */
export interface FrontierApiError {
  detail: string;
}