"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  generate,
  getGenerationExecution,
  getGenerationHealth,
  streamGeneration,
} from "../api";

import type {
  GenerationCitation,
  GenerationHealth,
  GenerationRequest,
  GenerationResponse,
  GenerationStatus,
  GenerationStreamChunk,
  GenerationTraceEvent,
  GenerationVerification,
  GraphEvidence,
  ResearchPlan,
  RetrievedEvidence,
} from "../types";

export interface UseGenerationOptions {
  streaming?: boolean;

  checkHealth?: boolean;
}

export interface UseGenerationReturn {
  response: GenerationResponse | null;

  answer: string;

  status: GenerationStatus;

  loading: boolean;

  streaming: boolean;

  error: string | null;

  citations: GenerationCitation[];

  verification: GenerationVerification | null;

  trace: GenerationTraceEvent[];

  health: GenerationHealth | null;

  /**
   * Evidence actually supplied to generation.
   */
  retrievedEvidence: RetrievedEvidence[];

  graphEvidence: GraphEvidence[];

  researchPlan: ResearchPlan | null;

  generate: (
    payload: GenerationRequest,
  ) => Promise<GenerationResponse | null>;

  generateStream: (
    payload: GenerationRequest,
  ) => Promise<GenerationResponse | null>;

  getExecution: (
    executionId: string,
  ) => Promise<GenerationResponse | null>;

  checkHealth: () => Promise<GenerationHealth | null>;

  cancel: () => void;

  reset: () => void;
}

export function useGeneration(
  options: UseGenerationOptions = {},
): UseGenerationReturn {
  const {
    streaming: defaultStreaming = false,
    checkHealth: checkHealthOnMount = false,
  } = options;

  const [response, setResponse] =
    useState<GenerationResponse | null>(null);

  const [answer, setAnswer] = useState("");

  const [status, setStatus] =
    useState<GenerationStatus>("idle");

  const [loading, setLoading] =
    useState(false);

  const [isStreaming, setIsStreaming] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [citations, setCitations] =
    useState<GenerationCitation[]>([]);

  const [verification, setVerification] =
    useState<GenerationVerification | null>(null);

  const [trace, setTrace] =
    useState<GenerationTraceEvent[]>([]);

  const [health, setHealth] =
    useState<GenerationHealth | null>(null);

  const [
    retrievedEvidence,
    setRetrievedEvidence,
  ] = useState<RetrievedEvidence[]>([]);

  const [graphEvidence, setGraphEvidence] =
    useState<GraphEvidence[]>([]);

  const [researchPlan, setResearchPlan] =
    useState<ResearchPlan | null>(null);

  const abortControllerRef =
    useRef<AbortController | null>(null);

  /* ------------------------------------------------------------------------ */
  /* Context                                                                  */
  /* ------------------------------------------------------------------------ */

  const setResearchContext = useCallback(
    (payload: GenerationRequest) => {
      setRetrievedEvidence(
        payload.retrieved_evidence || [],
      );

      setGraphEvidence(
        payload.graph_evidence || [],
      );

      setResearchPlan(
        payload.research_plan || null,
      );

      setCitations(
        payload.citations || [],
      );

      setVerification(
        payload.verification || null,
      );
    },
    [],
  );

  /* ------------------------------------------------------------------------ */
  /* Reset                                                                    */
  /* ------------------------------------------------------------------------ */

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();

    abortControllerRef.current = null;

    setResponse(null);
    setAnswer("");
    setStatus("idle");
    setLoading(false);
    setIsStreaming(false);
    setError(null);

    setCitations([]);
    setVerification(null);
    setTrace([]);

    setRetrievedEvidence([]);
    setGraphEvidence([]);
    setResearchPlan(null);
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Standard generation                                                      */
  /* ------------------------------------------------------------------------ */

  const runGeneration = useCallback(
    async (
      payload: GenerationRequest,
    ): Promise<GenerationResponse | null> => {
      abortControllerRef.current?.abort();

      const controller =
        new AbortController();

      abortControllerRef.current = controller;

      setLoading(true);
      setIsStreaming(false);
      setStatus("running");
      setError(null);

      setResponse(null);
      setAnswer("");
      setTrace([]);

      setResearchContext(payload);

      try {
        const result = await generate(payload);

        if (controller.signal.aborted) {
          return null;
        }

        setResponse(result);

        setAnswer(result.answer || "");

        setStatus(
          result.status || "completed",
        );

        setCitations(
          result.citations || [],
        );

        setVerification(
          result.verification || null,
        );

        setTrace(result.trace || []);

        if (result.error) {
          setError(result.error);
        }

        return result;
      } catch (err) {
        if (controller.signal.aborted) {
          return null;
        }

        const message =
          err instanceof Error
            ? err.message
            : "Generation failed.";

        setStatus("failed");
        setError(message);

        return null;
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    },
    [setResearchContext],
  );

  /* ------------------------------------------------------------------------ */
  /* Streaming generation                                                     */
  /* ------------------------------------------------------------------------ */

  const runGenerationStream =
    useCallback(
      async (
        payload: GenerationRequest,
      ): Promise<GenerationResponse | null> => {
        abortControllerRef.current?.abort();

        const controller =
          new AbortController();

        abortControllerRef.current =
          controller;

        setLoading(true);
        setIsStreaming(true);
        setStatus("running");
        setError(null);

        setResponse(null);
        setAnswer("");
        setTrace([]);

        setResearchContext(payload);

        let finalResponse:
          | GenerationResponse
          | null = null;

        let streamedAnswer = "";

        try {
          await streamGeneration(
            payload,
            {
              onStart: () => {
                setStatus("running");
              },

              onToken: (content) => {
                streamedAnswer += content;

                setAnswer(
                  streamedAnswer,
                );
              },

              onCitation: (
                chunk: GenerationStreamChunk,
              ) => {
                if (!chunk.citation) {
                  return;
                }

                setCitations(
                  (previous) => [
                    ...previous,
                    chunk.citation!,
                  ],
                );
              },

              onVerification: (
                chunk: GenerationStreamChunk,
              ) => {
                if (!chunk.verification) {
                  return;
                }

                setVerification(
                  chunk.verification,
                );
              },

              onTrace: (
                chunk: GenerationStreamChunk,
              ) => {
                if (!chunk.trace) {
                  return;
                }

                setTrace(
                  (previous) => [
                    ...previous,
                    chunk.trace!,
                  ],
                );
              },

              onComplete: (result) => {
                finalResponse = result;

                setResponse(result);

                setAnswer(
                  result.answer || "",
                );

                setStatus(
                  result.status ||
                    "completed",
                );

                setCitations(
                  result.citations || [],
                );

                setVerification(
                  result.verification ||
                    null,
                );

                setTrace(
                  result.trace || [],
                );
              },

              onError: (streamError) => {
                setStatus("failed");
                setError(
                  streamError.message,
                );
              },
            },
            controller.signal,
          );

          if (controller.signal.aborted) {
            return null;
          }

          if (finalResponse) {
            return finalResponse;
          }

          const fallbackResponse:
            GenerationResponse = {
            id: crypto.randomUUID(),

            status: "completed",

            answer: streamedAnswer,

            citations,

            verification:
              verification ||
              undefined,

            trace,

            evidence_used: {
              retrieved:
                retrievedEvidence.map(
                  (item) => item.id,
                ),

              graph:
                graphEvidence.map(
                  (item) => item.id,
                ),

              citations:
                citations.map(
                  (item) => item.id,
                ),

              verification_claims:
                verification?.claims.map(
                  (claim) => claim.id,
                ) || [],
            },
          };

          setResponse(fallbackResponse);

          setStatus("completed");

          return fallbackResponse;
        } catch (err) {
          if (controller.signal.aborted) {
            return null;
          }

          const message =
            err instanceof Error
              ? err.message
              : "Streaming generation failed.";

          setStatus("failed");
          setError(message);

          return null;
        } finally {
          if (!controller.signal.aborted) {
            setLoading(false);
            setIsStreaming(false);
          }
        }
      },
      [
        citations,
        graphEvidence,
        researchPlan,
        retrievedEvidence,
        setResearchContext,
        trace,
        verification,
      ],
    );

  /* ------------------------------------------------------------------------ */
  /* Public generation                                                        */
  /* ------------------------------------------------------------------------ */

  const handleGenerate = useCallback(
    async (
      payload: GenerationRequest,
    ): Promise<GenerationResponse | null> => {
      if (defaultStreaming) {
        return runGenerationStream(payload);
      }

      return runGeneration(payload);
    },
    [
      defaultStreaming,
      runGeneration,
      runGenerationStream,
    ],
  );

  const handleGenerateStream =
    useCallback(
      async (
        payload: GenerationRequest,
      ): Promise<GenerationResponse | null> => {
        return runGenerationStream(payload);
      },
      [runGenerationStream],
    );

  /* ------------------------------------------------------------------------ */
  /* Execution                                                                */
  /* ------------------------------------------------------------------------ */

  const handleGetExecution =
    useCallback(
      async (
        executionId: string,
      ): Promise<GenerationResponse | null> => {
        setLoading(true);
        setError(null);

        try {
          const execution =
            await getGenerationExecution(
              executionId,
            );

          if (!execution.response) {
            setStatus(execution.status);
            return null;
          }

          const result =
            execution.response;

          setResponse(result);

          setAnswer(
            result.answer || "",
          );

          setStatus(result.status);

          setCitations(
            result.citations || [],
          );

          setVerification(
            result.verification ||
              null,
          );

          setTrace(
            result.trace || [],
          );

          return result;
        } catch (err) {
          const message =
            err instanceof Error
              ? err.message
              : "Failed to load generation execution.";

          setError(message);

          return null;
        } finally {
          setLoading(false);
        }
      },
      [],
    );

  /* ------------------------------------------------------------------------ */
  /* Health                                                                   */
  /* ------------------------------------------------------------------------ */

  const handleCheckHealth =
    useCallback(
      async (): Promise<
        GenerationHealth | null
      > => {
        try {
          const result =
            await getGenerationHealth();

          setHealth(result);

          return result;
        } catch (err) {
          const message =
            err instanceof Error
              ? err.message
              : "Unable to check generation health.";

          setHealth({
            status: "unhealthy",
            message,
          });

          return null;
        }
      },
      [],
    );

  /* ------------------------------------------------------------------------ */
  /* Health on mount                                                          */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (!checkHealthOnMount) {
      return;
    }

    void handleCheckHealth();
  }, [
    checkHealthOnMount,
    handleCheckHealth,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Cleanup                                                                  */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  /* ------------------------------------------------------------------------ */
  /* Return                                                                   */
  /* ------------------------------------------------------------------------ */

  return {
    response,
    answer,
    status,
    loading,
    streaming: isStreaming,
    error,

    citations,
    verification,
    trace,

    health,

    retrievedEvidence,
    graphEvidence,
    researchPlan,

    generate: handleGenerate,

    generateStream:
      handleGenerateStream,

    getExecution:
      handleGetExecution,

    checkHealth:
      handleCheckHealth,

    cancel: () => {
      abortControllerRef.current?.abort();

      abortControllerRef.current = null;

      setLoading(false);
      setIsStreaming(false);
      setStatus("idle");
    },

    reset,
  };
}

export default useGeneration;