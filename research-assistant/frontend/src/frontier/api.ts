import type {
  FrontierOverview,
  Gap,
  NoveltyAnalysis,
  Trend,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      message || `Request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

/**
 * Get an overview of the current research frontier.
 */
export async function getFrontier(
  params?: {
    topic?: string;
    limit?: number;
  },
): Promise<FrontierOverview> {
  const searchParams = new URLSearchParams();

  if (params?.topic) {
    searchParams.set("topic", params.topic);
  }

  if (params?.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }

  const query = searchParams.toString();

  return request<FrontierOverview>(
    `/frontier${query ? `?${query}` : ""}`,
  );
}

/**
 * Get research trends.
 */
export async function getTrends(
  params?: {
    topic?: string;
    limit?: number;
    period?: string;
  },
): Promise<Trend[]> {
  const searchParams = new URLSearchParams();

  if (params?.topic) {
    searchParams.set("topic", params.topic);
  }

  if (params?.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }

  if (params?.period) {
    searchParams.set("period", params.period);
  }

  const query = searchParams.toString();

  return request<Trend[]>(
    `/frontier/trends${query ? `?${query}` : ""}`,
  );
}

/**
 * Detect research gaps.
 */
export async function getGaps(
  params?: {
    topic?: string;
    limit?: number;
    minConfidence?: number;
  },
): Promise<Gap[]> {
  const searchParams = new URLSearchParams();

  if (params?.topic) {
    searchParams.set("topic", params.topic);
  }

  if (params?.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }

  if (params?.minConfidence !== undefined) {
    searchParams.set(
      "min_confidence",
      String(params.minConfidence),
    );
  }

  const query = searchParams.toString();

  return request<Gap[]>(
    `/frontier/gaps${query ? `?${query}` : ""}`,
  );
}

/**
 * Analyze novelty for a research topic or query.
 */
export async function getNovelty(
  params: {
    query: string;
    topic?: string;
  },
): Promise<NoveltyAnalysis> {
  return request<NoveltyAnalysis>("/frontier/novelty", {
    method: "POST",
    body: JSON.stringify(params),
  });
}