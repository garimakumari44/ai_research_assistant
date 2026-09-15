
import { apiFetch } from "@/lib/api";

import type {
  Paper,
  PaperCreate,
  PaperUpdate,
  PaperSearchParams,
  PaperListResponse,
  PaperSearchResponse,
  PaperSearchResult,
} from "@/types/paper";

/* ========================================================================== */
/* Query helpers                                                              */
/* ========================================================================== */

/**
 * Builds a query string while ignoring:
 * - undefined
 * - null
 * - empty strings
 */
function buildQueryString(
  params: PaperSearchParams = {},
): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== null &&
      value !== ""
    ) {
      searchParams.set(
        key,
        String(value),
      );
    }
  });

  const queryString =
    searchParams.toString();

  return queryString
    ? `?${queryString}`
    : "";
}

/* ========================================================================== */
/* Get papers                                                                 */
/* ========================================================================== */

/**
 * GET /api/v1/papers
 *
 * Used for canonical paginated paper lists.
 *
 * This endpoint uses `query`, unlike the dedicated
 * search endpoint which uses `q`.
 */
export async function getPapers(
  params: PaperSearchParams = {},
): Promise<PaperListResponse> {
  const queryString =
    buildQueryString(params);

  return apiFetch<PaperListResponse>(
    `/papers${queryString}`,
  );
}

/* ========================================================================== */
/* Search papers                                                              */
/* ========================================================================== */

/**
 * GET /api/v1/papers/search
 *
 * Dedicated paper search endpoint.
 *
 * IMPORTANT:
 * The backend search endpoint expects `q`,
 * not `query`.
 *
 * Supported filters:
 * - q
 * - page
 * - page_size
 * - year
 * - venue
 * - author
 * - doi
 * - source
 * - provider
 * - provider_paper_id
 * - category
 * - published_from
 * - published_to
 * - sort_by
 * - sort_order
 */
export async function searchPapers(
  params: PaperSearchParams = {},
): Promise<PaperSearchResponse> {
  const searchParams =
    new URLSearchParams();

  /* ---------------------------------------------------------------------- */
  /* Query                                                                  */
  /* ---------------------------------------------------------------------- */

  const query =
    params.query?.trim();

  if (query) {
    searchParams.set(
      "q",
      query,
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Pagination                                                             */
  /* ---------------------------------------------------------------------- */

  if (
    params.page !== undefined
  ) {
    searchParams.set(
      "page",
      String(params.page),
    );
  }

  if (
    params.page_size !== undefined
  ) {
    searchParams.set(
      "page_size",
      String(params.page_size),
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Basic filters                                                          */
  /* ---------------------------------------------------------------------- */

  if (
    params.year !== undefined
  ) {
    searchParams.set(
      "year",
      String(params.year),
    );
  }

  if (params.venue?.trim()) {
    searchParams.set(
      "venue",
      params.venue.trim(),
    );
  }

  if (params.author?.trim()) {
    searchParams.set(
      "author",
      params.author.trim(),
    );
  }

  if (params.doi?.trim()) {
    searchParams.set(
      "doi",
      params.doi.trim(),
    );
  }

  if (params.source?.trim()) {
    searchParams.set(
      "source",
      params.source.trim(),
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Provider filters                                                       */
  /* ---------------------------------------------------------------------- */

  if (params.provider?.trim()) {
    searchParams.set(
      "provider",
      params.provider.trim(),
    );
  }

  if (
    params.provider_paper_id?.trim()
  ) {
    searchParams.set(
      "provider_paper_id",
      params.provider_paper_id.trim(),
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Category                                                               */
  /* ---------------------------------------------------------------------- */

  if (params.category?.trim()) {
    searchParams.set(
      "category",
      params.category.trim(),
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Publication date range                                                 */
  /* ---------------------------------------------------------------------- */

  if (params.published_from) {
    searchParams.set(
      "published_from",
      params.published_from,
    );
  }

  if (params.published_to) {
    searchParams.set(
      "published_to",
      params.published_to,
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Sorting                                                                */
  /* ---------------------------------------------------------------------- */

  if (params.sort_by?.trim()) {
    searchParams.set(
      "sort_by",
      params.sort_by.trim(),
    );
  }

  if (params.sort_order) {
    searchParams.set(
      "sort_order",
      params.sort_order,
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Request                                                                */
  /* ---------------------------------------------------------------------- */

  const queryString =
    searchParams.toString();

  return apiFetch<PaperSearchResponse>(
    `/papers/search${
      queryString
        ? `?${queryString}`
        : ""
    }`,
  );
}

/* ========================================================================== */
/* Search-result mapper                                                       */
/* ========================================================================== */

/**
 * Converts the canonical Paper object into
 * the UI-friendly search-result shape.
 */
export function toPaperSearchResult(
  paper: Paper,
): PaperSearchResult {
  return {
    id: paper.id,

    title: paper.title,

    abstract:
      paper.abstract ?? null,

    authors:
      (paper.authors ?? []).map(
        (author) =>
          typeof author === "string"
            ? author
            : author.name ??
              author.full_name ??
              "Unknown",
      ),

    publication_date:
      paper.publication_date ??
      null,

    venue:
      typeof paper.venue === "string"
        ? paper.venue
        : paper.venue?.name ??
          null,

    doi:
      paper.doi ?? null,

    url:
      paper.url ?? null,

    pdf_url:
      paper.pdf_url ?? null,

    citation_count:
      paper.citation_count ?? 0,

    reference_count:
      paper.reference_count ?? 0,

    source:
      paper.source ?? null,

    relevance_score:
      null,
  };
}

/* ========================================================================== */
/* Get UI search results                                                      */
/* ========================================================================== */

/**
 * Gets results from the dedicated search endpoint.
 *
 * IMPORTANT:
 * Do not call getPapers() here.
 *
 * getPapers() calls:
 *   GET /papers
 *
 * This function must call:
 *   GET /papers/search?q=...
 */
export async function getPaperSearchResults(
  params: PaperSearchParams = {},
): Promise<PaperSearchResponse> {
  return searchPapers(params);
}

/* ========================================================================== */
/* Get single paper                                                           */
/* ========================================================================== */

/**
 * GET /api/v1/papers/{paper_id}
 */
export async function getPaper(
  paperId: string,
): Promise<Paper> {
  if (!paperId) {
    throw new Error(
      "paperId is required",
    );
  }

  return apiFetch<Paper>(
    `/papers/${encodeURIComponent(
      paperId,
    )}`,
  );
}

/* ========================================================================== */
/* Create paper                                                               */
/* ========================================================================== */

/**
 * POST /api/v1/papers
 */
export async function createPaper(
  data: PaperCreate,
): Promise<Paper> {
  return apiFetch<Paper>(
    "/papers",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/* ========================================================================== */
/* Update paper                                                               */
/* ========================================================================== */

/**
 * PATCH /api/v1/papers/{paper_id}
 */
export async function updatePaper(
  paperId: string,
  data: PaperUpdate,
): Promise<Paper> {
  if (!paperId) {
    throw new Error(
      "paperId is required",
    );
  }

  return apiFetch<Paper>(
    `/papers/${encodeURIComponent(
      paperId,
    )}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    },
  );
}

/* ========================================================================== */
/* Delete paper                                                               */
/* ========================================================================== */

/**
 * DELETE /api/v1/papers/{paper_id}
 */
export async function deletePaper(
  paperId: string,
): Promise<void> {
  if (!paperId) {
    throw new Error(
      "paperId is required",
    );
  }

  await apiFetch<void>(
    `/papers/${encodeURIComponent(
      paperId,
    )}`,
    {
      method: "DELETE",
    },
  );
}

