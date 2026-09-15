
/* ========================================================================== */
/* Paper identifiers                                                          */
/* ========================================================================== */

export type PaperId = string;

/* ========================================================================== */
/* Authors                                                                    */
/* ========================================================================== */

export interface PaperAuthor {
  id?: number | string | null;
  name?: string | null;
  full_name?: string | null;
  author_id?: string | null;
  orcid?: string | null;
  email?: string | null;
  affiliation?: string | null;
  position?: number | null;
}

/* ========================================================================== */
/* Venue                                                                      */
/* ========================================================================== */

export interface PaperVenue {
  id?: number | string | null;
  name?: string | null;
  title?: string | null;
  display_name?: string | null;
}

/* ========================================================================== */
/* Paper                                                                      */
/* ========================================================================== */

export interface Paper {
  id: PaperId | null;

  title: string;

  abstract: string | null;

  authors: PaperAuthor[];

  publication_date: string | null;

  venue:
    | string
    | PaperVenue
    | null;

  journal: string | null;

  conference: string | null;

  doi: string | null;

  url: string | null;

  pdf_url: string | null;

  language: string | null;

  keywords: string[];

  categories: string[];

  external_ids: Record<
    string,
    string
  >;

  citation_count: number;

  reference_count: number;

  source: string | null;

  metadata: Record<
    string,
    unknown
  >;

  created_at: string | null;

  updated_at: string | null;

  canonical_key: string | null;
}

/* ========================================================================== */
/* Create                                                                     */
/* ========================================================================== */

export interface PaperCreate {
  title: string;

  abstract?: string | null;

  authors?: PaperAuthor[];

  publication_date?:
    | string
    | null;

  venue?: string | null;

  journal?: string | null;

  conference?: string | null;

  doi?: string | null;

  url?: string | null;

  pdf_url?: string | null;

  language?: string | null;

  keywords?: string[];

  categories?: string[];

  citation_count?: number;

  reference_count?: number;

  metadata?: Record<
    string,
    unknown
  >;
}

/* ========================================================================== */
/* Update                                                                     */
/* ========================================================================== */

export interface PaperUpdate {
  title?: string | null;

  abstract?: string | null;

  authors?: PaperAuthor[];

  publication_date?:
    | string
    | null;

  venue?: string | null;

  journal?: string | null;

  conference?: string | null;

  doi?: string | null;

  url?: string | null;

  pdf_url?: string | null;

  language?: string | null;

  keywords?: string[];

  categories?: string[];

  citation_count?: number;

  reference_count?: number;

  metadata?: Record<
    string,
    unknown
  >;
}

/* ========================================================================== */
/* Search parameters                                                          */
/* ========================================================================== */

/**
 * Parameters supported by:
 *
 * GET /api/v1/papers
 * GET /api/v1/papers/search
 */
export interface PaperSearchParams {
  /**
   * Free-text search.
   *
   * For /papers/search this is serialized
   * as `q`.
   *
   * For /papers it is serialized as `query`.
   */
  query?: string;

  author?: string;

  doi?: string;

  source?: string;

  /**
   * Provider name.
   *
   * Examples:
   * - arxiv
   * - openalex
   * - semantic_scholar
   * - crossref
   */
  provider?: string;

  /**
   * Provider-specific external paper ID.
   */
  provider_paper_id?: string;

  venue?: string;

  category?: string;

  year?: number;

  published_from?: string;

  published_to?: string;

  page?: number;

  page_size?: number;

  sort_by?: string;

  sort_order?:
    | "asc"
    | "desc";
}

/* ========================================================================== */
/* Search result                                                              */
/* ========================================================================== */

export interface PaperSearchResult {
  id: PaperId | null;

  title: string;

  abstract: string | null;

  authors: string[];

  publication_date: string | null;

  venue: string | null;

  doi: string | null;

  url: string | null;

  pdf_url: string | null;

  citation_count: number;

  reference_count?: number;

  source: string | null;

  relevance_score:
    | number
    | null;
}

/* ========================================================================== */
/* Search response                                                            */
/* ========================================================================== */

export interface PaperSearchResponse {
  papers: PaperSearchResult[];

  total: number;

  page: number;

  page_size: number;

  total_pages: number;
}

/* ========================================================================== */
/* List response                                                              */
/* ========================================================================== */

export interface PaperListResponse {
  items: Paper[];

  total: number;

  page: number;

  page_size: number;

  pages: number;
}

