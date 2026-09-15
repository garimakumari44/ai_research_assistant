/**
 * Research collection domain types.
 */

export type CollectionVisibility =
  | "private"
  | "shared"
  | "public";

export type CollectionItemType =
  | "paper"
  | "document"
  | "chunk"
  | "author"
  | "topic"
  | "dataset"
  | "report";

export interface Collection {
  id: string;

  name: string;

  description?: string | null;

  owner_id?: string | null;

  visibility?: CollectionVisibility;

  item_count?: number;

  paper_count?: number;
  document_count?: number;

  tags?: string[];

  metadata?: Record<string, unknown>;

  created_at: string;
  updated_at: string;
}

export interface CollectionItem {
  id: string;

  collection_id: string;

  item_id: string;

  item_type: CollectionItemType;

  title?: string | null;

  description?: string | null;

  metadata?: Record<string, unknown>;

  added_at?: string | null;
}

export interface CollectionDetail extends Collection {
  items: CollectionItem[];

  total_items?: number;

  page?: number;
  page_size?: number;
}

export interface CollectionCreateRequest {
  name: string;

  description?: string;

  visibility?: CollectionVisibility;

  tags?: string[];

  metadata?: Record<string, unknown>;
}

export interface CollectionUpdateRequest {
  name?: string;

  description?: string;

  visibility?: CollectionVisibility;

  tags?: string[];

  metadata?: Record<string, unknown>;
}

export interface CollectionItemRequest {
  item_id: string;

  item_type: CollectionItemType;
}

export interface CollectionListResponse {
  collections: Collection[];

  total: number;

  page?: number;
  page_size?: number;
}

export interface CollectionResponse {
  collection: Collection;
}

export interface CollectionDetailResponse {
  collection: CollectionDetail;
}