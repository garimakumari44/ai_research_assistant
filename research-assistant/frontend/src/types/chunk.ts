/**
 * Canonical frontend types for document chunks.
 *
 * A Chunk is the smallest indexed document unit used by:
 *
 *   Document
 *      ↓
 *   Section
 *      ↓
 *   Chunk
 *      ↓
 *   Embedding / Keyword Index
 *      ↓
 *   Retrieval
 *      ↓
 *   Evidence / Provenance
 *
 * Chunks may also participate in the knowledge graph through
 * graph references.
 */

/* -------------------------------------------------------------------------- */
/* Shared types                                                               */
/* -------------------------------------------------------------------------- */

export type ChunkId = string;

export type ChunkMetadata = Record<string, unknown>;

/**
 * Chunking strategy used by the document pipeline.
 */
export type ChunkStrategy =
  | "fixed"
  | "recursive"
  | "semantic"
  | "section"
  | "paragraph"
  | "structural"
  | "custom"
  | string;

/**
 * Embedding/indexing state.
 */
export type EmbeddingStatus =
  | "pending"
  | "processing"
  | "indexed"
  | "failed";

/**
 * Optional graph relationship attached to a chunk.
 */
export interface ChunkGraphReference {
  node_id: string;

  node_type: string;

  node_label?: string | null;

  relationship_type?: string | null;

  score?: number | null;

  metadata?: ChunkMetadata;
}

/* -------------------------------------------------------------------------- */
/* Core Chunk                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * Represents a retrieval chunk extracted from a paper document.
 */
export interface Chunk {
  id: ChunkId | null;

  document_id: string;

  /**
   * Parent section.
   */
  section_id: string | null;

  /**
   * Chunk text used for retrieval and embedding.
   */
  text: string;

  /**
   * Position inside the document.
   */
  position: number;

  /**
   * Position inside its section.
   */
  section_position: number | null;

  /**
   * Chunking strategy used.
   */
  chunk_strategy: ChunkStrategy;

  /**
   * Number of tokens.
   */
  token_count: number | null;

  /**
   * Character count.
   */
  character_count: number | null;

  /**
   * Page location.
   */
  start_page: number | null;

  end_page: number | null;

  /**
   * Character offsets in source document.
   */
  start_offset: number | null;

  end_offset: number | null;

  /**
   * Previous/next chunks.
   *
   * Useful for context expansion.
   */
  previous_chunk_id: string | null;

  next_chunk_id: string | null;

  /**
   * Vector embedding status.
   */
  embedding_status: EmbeddingStatus;

  /**
   * Vector database identifier.
   */
  embedding_id: string | null;

  /**
   * Optional graph entities associated with this chunk.
   */
  graph_references?: ChunkGraphReference[];

  /**
   * Arbitrary backend metadata.
   */
  metadata: ChunkMetadata;

  created_at: string | null;

  updated_at: string | null;
}

/* -------------------------------------------------------------------------- */
/* Create / Update                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Payload used to create a chunk.
 */
export interface ChunkCreate {
  document_id: string;

  section_id?: string | null;

  text: string;

  position?: number;

  section_position?: number | null;

  chunk_strategy?: ChunkStrategy;

  token_count?: number | null;

  character_count?: number | null;

  start_page?: number | null;

  end_page?: number | null;

  start_offset?: number | null;

  end_offset?: number | null;

  previous_chunk_id?: string | null;

  next_chunk_id?: string | null;

  embedding_status?: EmbeddingStatus;

  embedding_id?: string | null;

  graph_references?: ChunkGraphReference[];

  metadata?: ChunkMetadata;
}

/**
 * Payload used to update a chunk.
 */
export interface ChunkUpdate {
  section_id?: string | null;

  text?: string;

  position?: number;

  section_position?: number | null;

  chunk_strategy?: ChunkStrategy;

  token_count?: number | null;

  character_count?: number | null;

  start_page?: number | null;

  end_page?: number | null;

  start_offset?: number | null;

  end_offset?: number | null;

  previous_chunk_id?: string | null;

  next_chunk_id?: string | null;

  embedding_status?: EmbeddingStatus;

  embedding_id?: string | null;

  graph_references?: ChunkGraphReference[];

  metadata?: ChunkMetadata;
}

/* -------------------------------------------------------------------------- */
/* Summary                                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Lightweight representation for lists/results.
 */
export interface ChunkSummary {
  id: ChunkId | null;

  document_id: string;

  section_id: string | null;

  position: number;

  text: string;

  token_count: number | null;

  start_page: number | null;

  end_page: number | null;

  embedding_status: EmbeddingStatus;
}

/* -------------------------------------------------------------------------- */
/* Responses                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Backend chunk list response.
 */
export interface ChunkListResponse {
  items: Chunk[];

  total: number;

  page: number;

  page_size: number;

  pages: number;
}

/* -------------------------------------------------------------------------- */
/* Search                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Query parameters for chunks.
 */
export interface ChunkSearchParams {
  document_id?: string;

  section_id?: string;

  embedding_status?: EmbeddingStatus;

  page?: number;

  page_size?: number;

  sort_by?: string;

  sort_order?: "asc" | "desc";
}

/**
 * Result returned from semantic/vector search.
 */
export interface ChunkSearchResult {
  chunk: Chunk;

  /**
   * Similarity score returned by the vector database.
   */
  score: number;

  /**
   * Optional rank from retrieval.
   */
  rank?: number;

  paper_id?: string | null;

  paper_title?: string | null;

  section_title?: string | null;

  retrieval_method?: "semantic" | "keyword" | "graph" | "hybrid" | string;

  metadata?: ChunkMetadata;
}

/**
 * Response returned by chunk/vector search.
 */
export interface ChunkSearchResponse {
  items: ChunkSearchResult[];

  total: number;

  query: string;

  page: number;

  page_size: number;
}

/* -------------------------------------------------------------------------- */
/* Context expansion                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Context surrounding a selected chunk.
 */
export interface ChunkContext {
  chunk: Chunk;

  previous?: ChunkSummary[];

  next?: ChunkSummary[];

  section?: {
    id: string | null;
    title: string;
    section_type?: string | null;
  } | null;

  metadata?: ChunkMetadata;
}