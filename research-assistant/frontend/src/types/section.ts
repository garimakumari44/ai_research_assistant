/**
 * Canonical frontend types for parsed document sections.
 *
 * Document
 *    ↓
 * Section hierarchy
 *    ↓
 * Chunk
 *
 * Sections are structural units used by:
 *
 *   document viewer
 *   structural chunking
 *   retrieval filters
 *   evidence/provenance
 *   research navigation
 */

/* -------------------------------------------------------------------------- */
/* Shared                                                                      */
/* -------------------------------------------------------------------------- */

export type SectionId = string;

export type SectionMetadata = Record<string, unknown>;

/**
 * Common section types produced by the document parser.
 */
export type SectionType =
  | "abstract"
  | "introduction"
  | "background"
  | "related_work"
  | "methodology"
  | "methods"
  | "approach"
  | "experiments"
  | "results"
  | "discussion"
  | "conclusion"
  | "references"
  | "appendix"
  | "acknowledgements"
  | "unknown"
  | string;

/* -------------------------------------------------------------------------- */
/* Section                                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Represents a logical section inside a paper document.
 */
export interface Section {
  id: SectionId | null;

  document_id: string;

  /**
   * Parent section.
   */
  parent_id: string | null;

  /**
   * Human-readable title.
   */
  title: string;

  /**
   * Normalized section type.
   */
  section_type: SectionType;

  /**
   * Hierarchical level.
   *
   * 0 = document/root
   * 1 = major section
   * 2 = subsection
   * 3 = sub-subsection
   */
  level: number;

  /**
   * Position within the document.
   */
  position: number;

  /**
   * Original section number.
   */
  section_number: string | null;

  /**
   * Extracted text belonging to this section.
   */
  text: string;

  /**
   * First page.
   */
  start_page: number | null;

  /**
   * Last page.
   */
  end_page: number | null;

  /**
   * Character offsets.
   */
  start_offset: number | null;

  end_offset: number | null;

  /**
   * Number of chunks generated from this section.
   */
  chunk_count: number;

  /**
   * Child section count.
   */
  child_count?: number;

  metadata: SectionMetadata;

  created_at: string | null;

  updated_at: string | null;
}

/* -------------------------------------------------------------------------- */
/* Create / Update                                                             */
/* -------------------------------------------------------------------------- */

export interface SectionCreate {
  document_id: string;

  parent_id?: string | null;

  title: string;

  section_type?: SectionType;

  level?: number;

  position?: number;

  section_number?: string | null;

  text?: string;

  start_page?: number | null;

  end_page?: number | null;

  start_offset?: number | null;

  end_offset?: number | null;

  metadata?: SectionMetadata;
}

export interface SectionUpdate {
  parent_id?: string | null;

  title?: string;

  section_type?: SectionType;

  level?: number;

  position?: number;

  section_number?: string | null;

  text?: string;

  start_page?: number | null;

  end_page?: number | null;

  start_offset?: number | null;

  end_offset?: number | null;

  chunk_count?: number;

  metadata?: SectionMetadata;
}

/* -------------------------------------------------------------------------- */
/* Summary                                                                     */
/* -------------------------------------------------------------------------- */

export interface SectionSummary {
  id: SectionId | null;

  document_id: string;

  parent_id: string | null;

  title: string;

  section_type: SectionType;

  level: number;

  position: number;

  section_number: string | null;

  start_page: number | null;

  end_page: number | null;

  chunk_count: number;
}

/* -------------------------------------------------------------------------- */
/* Tree                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Section tree used by the document viewer.
 */
export interface SectionTreeNode extends Section {
  children: SectionTreeNode[];
}

/**
 * Root document structure.
 */
export interface SectionTree {
  document_id: string;

  sections: SectionTreeNode[];

  total_sections: number;

  max_depth?: number;
}

/* -------------------------------------------------------------------------- */
/* Responses                                                                   */
/* -------------------------------------------------------------------------- */

export interface SectionListResponse {
  items: Section[];

  total: number;

  page: number;

  page_size: number;

  pages: number;
}

/* -------------------------------------------------------------------------- */
/* Search                                                                      */
/* -------------------------------------------------------------------------- */

export interface SectionSearchParams {
  document_id?: string;

  parent_id?: string | null;

  section_type?: SectionType;

  level?: number;

  page?: number;

  page_size?: number;

  sort_by?: string;

  sort_order?: "asc" | "desc";
}

/* -------------------------------------------------------------------------- */
/* Section navigation                                                          */
/* -------------------------------------------------------------------------- */

export interface SectionNavigationItem {
  id: SectionId;

  title: string;

  section_number: string | null;

  level: number;

  position: number;

  parent_id: string | null;

  start_page: number | null;

  end_page: number | null;

  has_children: boolean;
}

/**
 * Flattened section navigation used by sidebars/document viewers.
 */
export interface SectionNavigation {
  document_id: string;

  items: SectionNavigationItem[];

  active_section_id?: SectionId | null;
}

/* -------------------------------------------------------------------------- */
/* Section statistics                                                          */
/* -------------------------------------------------------------------------- */

export interface SectionStatistics {
  section_id: SectionId;

  chunk_count: number;

  child_count: number;

  text_length?: number;

  page_count?: number;

  metadata?: SectionMetadata;
}