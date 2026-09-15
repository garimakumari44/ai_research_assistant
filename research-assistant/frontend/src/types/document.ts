
/* -------------------------------------------------------------------------- */
/* Document                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Backend currently returns a document record with this shape:
 *
 * {
 *   id,
 *   filename,
 *   description,
 *   document_type,
 *   status,
 *   paper_id,
 *   metadata,
 *   created_at,
 *   updated_at
 * }
 */

export type DocumentId = string;

export type DocumentMetadata =
  Record<string, unknown>;

export type DocumentStatus =
  | "pending"
  | "resolving"
  | "downloading"
  | "downloaded"
  | "extracting"
  | "extracted"
  | "parsing"
  | "parsed"
  | "storing"
  | "completed"
  | "failed"
  | string;

export interface Document {
  id: DocumentId | null;

  /**
   * Original filename returned by the backend.
   */
  filename: string;

  /**
   * Optional document description.
   */
  description: string | null;

  /**
   * Backend document classification/type.
   */
  document_type: string | null;

  /**
   * Processing status.
   */
  status: DocumentStatus;

  /**
   * Associated research paper.
   */
  paper_id: number | string | null;

  /**
   * Additional backend metadata.
   */
  metadata: DocumentMetadata;

  created_at: string | null;

  updated_at: string | null;
}

/* -------------------------------------------------------------------------- */
/* Upload                                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Document upload request.
 *
 * The backend currently accepts the actual file as multipart/form-data.
 */
export interface DocumentUpload {
  file: File;
}

/* -------------------------------------------------------------------------- */
/* Summary                                                                    */
/* -------------------------------------------------------------------------- */

export interface DocumentSummary {
  id: DocumentId | null;

  filename: string;

  document_type: string | null;

  status: DocumentStatus;

  paper_id: number | string | null;

  created_at: string | null;

  updated_at: string | null;
}

/* -------------------------------------------------------------------------- */
/* Paper reference                                                            */
/* -------------------------------------------------------------------------- */

export interface PaperReference {
  id: string | number | null;

  title: string;

  doi: string | null;

  publication_date: string | null;
}

/* -------------------------------------------------------------------------- */
/* Document detail                                                            */
/* -------------------------------------------------------------------------- */

export interface DocumentDetail
  extends Document {
  paper?: PaperReference;
}

/* -------------------------------------------------------------------------- */
/* List response                                                              */
/* -------------------------------------------------------------------------- */

export interface DocumentListResponse {
  items: Document[];

  total: number;

  /**
   * These are optional because the current
   * backend list route only explicitly
   * constructs items + total.
   *
   * They can become required once pagination
   * is implemented server-side.
   */
  page?: number;

  page_size?: number;

  pages?: number;
}

/* -------------------------------------------------------------------------- */
/* Search                                                                     */
/* -------------------------------------------------------------------------- */

export interface DocumentSearchParams {
  paper_id?: number | string;

  status?: DocumentStatus;

  document_type?: string;

  page?: number;

  page_size?: number;

  sort_by?: string;

  sort_order?: "asc" | "desc";
}

