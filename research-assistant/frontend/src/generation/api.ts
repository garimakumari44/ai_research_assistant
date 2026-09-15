/**
 * Generation API client.
 *
 * Generation is the final synthesis API for the research pipeline.
 *
 * Research context:
 *
 *   Research Plan
 *        ↓
 *   Retrieved Evidence
 *        +
 *   Graph Evidence
 *        +
 *   Citations
 *        +
 *   Verification
 *        ↓
 *      Generation
 */

import { apiFetch } from "@/lib/api";

import type {
  GenerationExecution,
  GenerationExecutionList,
  GenerationHealth,
  GenerationRequest,
  GenerationResponse,
  GenerationStreamChunk,
} from "./types";

/* -------------------------------------------------------------------------- */
/* Generation                                                                  */
/* -------------------------------------------------------------------------- */

export async function generate(
  payload: GenerationRequest,
): Promise<GenerationResponse> {
  return apiFetch<GenerationResponse>(
    "/api/v1/generation/generate",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function generateAnswer(
  payload: GenerationRequest,
): Promise<GenerationResponse> {
  return generate(payload);
}

/* -------------------------------------------------------------------------- */
/* Execution                                                                   */
/* -------------------------------------------------------------------------- */

export async function getGenerationExecution(
  executionId: string,
): Promise<GenerationExecution> {
  return apiFetch<GenerationExecution>(
    `/api/v1/generation/executions/${encodeURIComponent(executionId)}`,
  );
}

export async function listGenerationExecutions(
  params?: {
    page?: number;
    page_size?: number;
    status?: string;
  },
): Promise<GenerationExecutionList> {
  const searchParams = new URLSearchParams();

  if (params?.page !== undefined) {
    searchParams.set("page", String(params.page));
  }

  if (params?.page_size !== undefined) {
    searchParams.set("page_size", String(params.page_size));
  }

  if (params?.status) {
    searchParams.set("status", params.status);
  }

  const query = searchParams.toString();

  return apiFetch<GenerationExecutionList>(
    `/api/v1/generation/executions${
      query ? `?${query}` : ""
    }`,
  );
}

export async function deleteGenerationExecution(
  executionId: string,
): Promise<void> {
  await apiFetch<void>(
    `/api/v1/generation/executions/${encodeURIComponent(executionId)}`,
    {
      method: "DELETE",
    },
  );
}

/* -------------------------------------------------------------------------- */
/* Health                                                                      */
/* -------------------------------------------------------------------------- */

export async function getGenerationHealth(): Promise<GenerationHealth> {
  return apiFetch<GenerationHealth>(
    "/api/v1/generation/health",
  );
}

/* -------------------------------------------------------------------------- */
/* Streaming                                                                   */
/* -------------------------------------------------------------------------- */

export async function streamGeneration(
  payload: GenerationRequest,
  handlers: {
    onStart?: (chunk: GenerationStreamChunk) => void;

    onToken?: (
      content: string,
      chunk: GenerationStreamChunk,
    ) => void;

    onCitation?: (
      chunk: GenerationStreamChunk,
    ) => void;

    onVerification?: (
      chunk: GenerationStreamChunk,
    ) => void;

    onTrace?: (
      chunk: GenerationStreamChunk,
    ) => void;

    onComplete?: (
      response: GenerationResponse,
    ) => void;

    onError?: (
      error: Error,
    ) => void;
  },
  signal?: AbortSignal,
): Promise<void> {
  try {
    const response = await fetch(
      "/api/v1/generation/generate/stream",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(payload),
        signal,
      },
    );

    if (!response.ok) {
      throw new Error(
        `Generation stream failed (${response.status})`,
      );
    }

    if (!response.body) {
      throw new Error(
        "Generation stream returned no response body.",
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, {
        stream: true,
      });

      const events = buffer.split("\n\n");

      buffer = events.pop() || "";

      for (const event of events) {
        const lines = event
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);

        const dataLine = lines.find((line) =>
          line.startsWith("data:"),
        );

        if (!dataLine) {
          continue;
        }

        const rawData = dataLine
          .slice(5)
          .trim();

        if (!rawData) {
          continue;
        }

        let chunk: GenerationStreamChunk;

        try {
          chunk =
            JSON.parse(rawData) as GenerationStreamChunk;
        } catch {
          continue;
        }

        switch (chunk.type) {
          case "start":
            handlers.onStart?.(chunk);
            break;

          case "token":
            handlers.onToken?.(
              chunk.content || "",
              chunk,
            );
            break;

          case "citation":
            handlers.onCitation?.(chunk);
            break;

          case "verification":
            handlers.onVerification?.(chunk);
            break;

          case "trace":
            handlers.onTrace?.(chunk);
            break;

          case "complete":
            if (chunk.response) {
              handlers.onComplete?.(
                chunk.response,
              );
            }
            break;

          case "error":
            handlers.onError?.(
              new Error(
                chunk.error ||
                  "Generation stream failed.",
              ),
            );
            break;
        }
      }
    }
  } catch (error) {
    const normalizedError =
      error instanceof Error
        ? error
        : new Error(
            "Generation request failed.",
          );

    handlers.onError?.(normalizedError);

    throw normalizedError;
  }
}

/* -------------------------------------------------------------------------- */
/* Default export                                                             */
/* -------------------------------------------------------------------------- */

export const generationApi = {
  generate,
  generateAnswer,
  streamGeneration,
  getGenerationExecution,
  listGenerationExecutions,
  deleteGenerationExecution,
  getGenerationHealth,
};

export default generationApi;