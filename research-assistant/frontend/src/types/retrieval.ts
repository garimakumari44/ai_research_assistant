/**
 * Canonical frontend types for the unified retrieval system.
 *
 * Retrieval supports:
 *
 *   semantic
 *   keyword
 *   graph
 *   hybrid
 *   fusion
 *   reranking
 *   evidence
 *   provenance
 *
 * Graph retrieval is a capability of the retrieval engine.
 *
 * It is NOT a separate Graph RAG API.
 */

/* -------------------------------------------------------------------------- */
/* Shared                                                                      */
/* -------------------------------------------------------------------------- */

export type UUID = string;

export type RetrievalMetadata = Record<string, unknown>;

export type RetrievalMethod =
  | "semantic"
  | "keyword"
  | "graph"
  | "hybrid"
  | "fusion"
  | "unknown"
  | string;

export type GraphNodeType =
  | "paper"
  | "author"
  | "method"
  | "dataset"
  | "topic"
  | "organization"
  | "venue"
  | "document"
  | "section"
  | "chunk"
  | "concept"
  | string;

/* -------------------------------------------------------------------------- */
/* Query Analysis                                                              */
/* -------------------------------------------------------------------------- */

export interface QueryAnalysis {
  original_query: string;

  normalized_query: string | null;

  keywords: string[];

  entities: string[];

  concepts: string[];

  filters: RetrievalMetadata;

  requires_semantic_search: boolean;

  requires_keyword_search: boolean;

  requires_graph_search?: boolean;

  query_type?: string | null;

  intent?: string | null;

  domain?: string | null;

  complexity?: number | null;
}

/* -------------------------------------------------------------------------- */
/* Classification                                                              */
/* -------------------------------------------------------------------------- */

export interface QueryClassification {
  query_type: string;

  intent: string;

  domain: string | null;

  confidence: number;

  labels: string[];
}

/* -------------------------------------------------------------------------- */
/* Graph provenance                                                            */
/* -------------------------------------------------------------------------- */

export interface GraphPathNode {
  id: UUID;

  type: GraphNodeType;

  label?: string | null;

  metadata?: RetrievalMetadata;
}

export interface GraphRelationship {
  id?: UUID | null;

  type: string;

  source_node_id: UUID;

  target_node_id: UUID;

  score?: number | null;

  metadata?: RetrievalMetadata;
}

/* -------------------------------------------------------------------------- */
/* Provenance                                                                  */
/* -------------------------------------------------------------------------- */

export interface Provenance {
  paper_id: UUID | null;

  document_id: UUID | null;

  chunk_id: UUID;

  page: number | null;

  section: string | null;

  section_id?: UUID | null;

  source: string | null;

  graph_node_id?: UUID | null;

  graph_node_type?: GraphNodeType | null;

  graph_edge_id?: UUID | null;

  graph_edge_type?: string | null;

  graph_path?: GraphPathNode[] | null;
}

/* -------------------------------------------------------------------------- */
/* Graph Evidence                                                              */
/* -------------------------------------------------------------------------- */

export interface GraphEvidence {
  evidence_id: UUID | null;

  content: string;

  score: number;

  rank: number | null;

  node_id: UUID | null;

  node_type: GraphNodeType | null;

  node_label: string | null;

  edge_id: UUID | null;

  edge_type: string | null;

  path: GraphPathNode[];

  relationships?: GraphRelationship[];

  provenance: Provenance | null;

  metadata: RetrievalMetadata;
}

/* -------------------------------------------------------------------------- */
/* Unified Evidence                                                            */
/* -------------------------------------------------------------------------- */

export interface Evidence {
  evidence_id: UUID | null;

  content: string;

  score: number;

  rank: number | null;

  provenance: Provenance;

  retrieval_method?: RetrievalMethod;

  graph?: GraphEvidence | null;

  metadata: RetrievalMetadata;
}

/* -------------------------------------------------------------------------- */
/* Retrieval Request                                                           */
/* -------------------------------------------------------------------------- */

export interface RetrievalRequest {
  query: string;

  paper_id?: UUID | null;

  document_id?: UUID | null;

  top_k?: number;

  vector_weight?: number;

  keyword_weight?: number;

  graph_enabled?: boolean;

  graph_depth?: number;

  graph_top_k?: number;

  retrieval_methods?: RetrievalMethod[];

  filters?: RetrievalMetadata;
}

/* -------------------------------------------------------------------------- */
/* Retrieval Result                                                            */
/* -------------------------------------------------------------------------- */

export interface RetrievalResult {
  chunk_id: UUID;

  document_id: UUID;

  paper_id: UUID | null;

  section_id: UUID | null;

  content: string;

  score: number;

  rank: number;

  retrieval_method: RetrievalMethod;

  rerank_score: number | null;

  vector_score: number | null;

  keyword_score: number | null;

  graph_score?: number | null;

  provenance: Provenance | null;

  evidence: Evidence | null;

  graph?: GraphEvidence | null;

  metadata: RetrievalMetadata;
}

/* -------------------------------------------------------------------------- */
/* Capability-specific results                                                */
/* -------------------------------------------------------------------------- */

export type SemanticRetrievalResult = RetrievalResult;

export type KeywordRetrievalResult = RetrievalResult;

export interface GraphRetrievalResult extends RetrievalResult {
  retrieval_method: "graph" | string;

  graph: GraphEvidence | null;

  graph_score: number | null;
}

/* -------------------------------------------------------------------------- */
/* Retrieval Response                                                          */
/* -------------------------------------------------------------------------- */

export interface RetrievalResponse {
  query: string;

  /**
   * Final fused/reranked results.
   */
  results: RetrievalResult[];

  semantic_results: SemanticRetrievalResult[];

  keyword_results: KeywordRetrievalResult[];

  graph_results: GraphRetrievalResult[];

  total: number;

  top_k: number;

  retrieval_mode: string;

  retrieval_methods?: RetrievalMethod[];

  query_analysis: QueryAnalysis | null;

  query_classification: QueryClassification | null;

  evidence: Evidence[];

  provenance?: Provenance[];

  graph_evidence?: GraphEvidence[];

  metadata: RetrievalMetadata;
}

/* -------------------------------------------------------------------------- */
/* Pipeline UI                                                                 */
/* -------------------------------------------------------------------------- */

export type RetrievalStage =
  | "idle"
  | "analyzing"
  | "classifying"
  | "planning"
  | "retrieving"
  | "semantic_retrieval"
  | "keyword_retrieval"
  | "graph_retrieval"
  | "fusing_results"
  | "reranking"
  | "collecting_evidence"
  | "resolving_provenance"
  | "completed"
  | "error";

export interface RetrievalPipelineStatus {
  stage: RetrievalStage;

  message?: string | null;

  progress?: number | null;

  completed?: boolean;

  error?: string | null;
}

/* -------------------------------------------------------------------------- */
/* Source citation                                                             */
/* -------------------------------------------------------------------------- */

export interface SourceCitation {
  paper_id: UUID | null;

  document_id: UUID | null;

  section_id?: UUID | null;

  chunk_id: UUID;

  page: number | null;

  section: string | null;

  source: string | null;

  graph_node_id?: UUID | null;

  graph_node_type?: GraphNodeType | null;

  graph_edge_id?: UUID | null;

  graph_edge_type?: string | null;
}

export function provenanceToCitation(
  provenance: Provenance,
): SourceCitation {
  return {
    paper_id: provenance.paper_id,

    document_id: provenance.document_id,

    chunk_id: provenance.chunk_id,

    page: provenance.page,

    section_id: provenance.section_id ?? null,

    section: provenance.section,

    source: provenance.source,

    graph_node_id: provenance.graph_node_id ?? null,

    graph_node_type: provenance.graph_node_type ?? null,

    graph_edge_id: provenance.graph_edge_id ?? null,

    graph_edge_type: provenance.graph_edge_type ?? null,
  };
}

/* -------------------------------------------------------------------------- */
/* Retrieval statistics                                                        */
/* -------------------------------------------------------------------------- */

export interface RetrievalStatistics {
  semantic_count: number;

  keyword_count: number;

  graph_count: number;

  fused_count: number;

  reranked_count: number;

  evidence_count: number;

  average_score?: number | null;

  graph_coverage?: number | null;

  metadata?: RetrievalMetadata;
}