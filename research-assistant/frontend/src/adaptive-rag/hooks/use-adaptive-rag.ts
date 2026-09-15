"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  executeAdaptiveRAG,
  getAdaptiveRAGStrategies,
  getGraphContext,
} from "../api";

import type {
  AdaptiveRAGRequest,
  AdaptiveRAGResponse,
  GraphContext,
  RAGStrategy,
  StrategyOption,
} from "../types";

/* -------------------------------------------------------------------------- */
/* Options                                                                    */
/* -------------------------------------------------------------------------- */

interface UseAdaptiveRAGOptions {
  initialStrategy?: RAGStrategy;

  autoLoadStrategies?: boolean;

  /**
   * Automatically preview graph context when graph_augmented
   * strategy is selected.
   */
  autoLoadGraphContext?: boolean;
}

/* -------------------------------------------------------------------------- */
/* Return Type                                                                */
/* -------------------------------------------------------------------------- */

interface UseAdaptiveRAGReturn {
  result: AdaptiveRAGResponse | null;

  strategies: StrategyOption[];

  graphContext: GraphContext | null;

  loading: boolean;

  loadingStrategies: boolean;

  loadingGraph: boolean;

  error: string | null;

  graphError: string | null;

  execute: (
    request: Omit<
      AdaptiveRAGRequest,
      "strategy"
    > & {
      strategy?: RAGStrategy;
    },
  ) => Promise<AdaptiveRAGResponse | null>;

  loadStrategies: () => Promise<
    StrategyOption[]
  >;

  loadGraphContext: (
    params?: {
      query?: string;

      node_ids?: string[];

      depth?: number;

      node_types?: string[];

      edge_types?: string[];

      limit?: number;
    },
  ) => Promise<GraphContext | null>;

  reset: () => void;
}

/* -------------------------------------------------------------------------- */
/* Hook                                                                       */
/* -------------------------------------------------------------------------- */

export function useAdaptiveRAG(
  options: UseAdaptiveRAGOptions = {},
): UseAdaptiveRAGReturn {
  const {
    initialStrategy = "auto",

    autoLoadStrategies = false,

    autoLoadGraphContext = false,
  } = options;

  const [result, setResult] =
    useState<AdaptiveRAGResponse | null>(
      null,
    );

  const [strategies, setStrategies] =
    useState<StrategyOption[]>([]);

  const [graphContext, setGraphContext] =
    useState<GraphContext | null>(
      null,
    );

  const [loading, setLoading] =
    useState(false);

  const [
    loadingStrategies,
    setLoadingStrategies,
  ] = useState(false);

  const [
    loadingGraph,
    setLoadingGraph,
  ] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [
    graphError,
    setGraphError,
  ] = useState<string | null>(null);

  const requestIdRef =
    useRef(0);

  const graphRequestIdRef =
    useRef(0);

  /* ------------------------------------------------------------------------ */
  /* Load Strategies                                                          */
  /* ------------------------------------------------------------------------ */

  const loadStrategies =
    useCallback(async () => {
      setLoadingStrategies(true);

      try {
        const response =
          await getAdaptiveRAGStrategies();

        setStrategies(response);

        return response;
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed to load Adaptive RAG strategies.";

        setError(message);

        return [];
      } finally {
        setLoadingStrategies(
          false,
        );
      }
    }, []);

  /* ------------------------------------------------------------------------ */
  /* Load Graph Context                                                       */
  /* ------------------------------------------------------------------------ */

  const loadGraphContext =
    useCallback(
      async (
        params: {
          query?: string;

          node_ids?: string[];

          depth?: number;

          node_types?: string[];

          edge_types?: string[];

          limit?: number;
        } = {},
      ) => {
        const requestId =
          ++graphRequestIdRef.current;

        setLoadingGraph(true);

        setGraphError(null);

        try {
          const response =
            await getGraphContext(
              params,
            );

          if (
            requestId !==
            graphRequestIdRef.current
          ) {
            return null;
          }

          setGraphContext(
            response,
          );

          return response;
        } catch (err) {
          if (
            requestId !==
            graphRequestIdRef.current
          ) {
            return null;
          }

          const message =
            err instanceof Error
              ? err.message
              : "Failed to load Research Graph context.";

          setGraphError(
            message,
          );

          setGraphContext(
            null,
          );

          return null;
        } finally {
          if (
            requestId ===
            graphRequestIdRef.current
          ) {
            setLoadingGraph(
              false,
            );
          }
        }
      },
      [],
    );

  /* ------------------------------------------------------------------------ */
  /* Execute Adaptive RAG                                                     */
  /* ------------------------------------------------------------------------ */

  const execute =
    useCallback(
      async (
        request: Omit<
          AdaptiveRAGRequest,
          "strategy"
        > & {
          strategy?: RAGStrategy;
        },
      ) => {
        const requestId =
          ++requestIdRef.current;

        setLoading(true);

        setError(null);

        /*
         * The selected strategy is resolved here.
         *
         * "auto" is passed through as adaptive=true.
         * graph_augmented automatically enables graph execution.
         */
        const strategy =
          request.strategy ??
          initialStrategy;

        const payload: AdaptiveRAGRequest =
          {
            ...request,

            strategy,

            adaptive:
              strategy === "auto"
                ? true
                : request.adaptive,

            enable_graph:
              strategy ===
              "graph_augmented"
                ? true
                : request.enable_graph,

            enable_multi_query:
              strategy ===
                "multi_query" ||
              strategy ===
                "iterative" ||
              strategy ===
                "corrective" ||
              strategy ===
                "graph_augmented"
                ? true
                : request.enable_multi_query,

            enable_correction:
              strategy ===
                "corrective" ||
              strategy ===
                "iterative" ||
              strategy ===
                "graph_augmented"
                ? true
                : request.enable_correction,
          };

        /*
         * Optional graph preview.
         *
         * This does NOT replace backend orchestration.
         * It gives the UI immediate graph context while the
         * Adaptive RAG execution remains the authoritative workflow.
         */
        if (
          autoLoadGraphContext &&
          strategy ===
            "graph_augmented" &&
          request.query
        ) {
          void loadGraphContext({
            query:
              request.query,

            depth:
              request.graph_depth ??
              2,

            node_types:
              request.graph_node_types,

            edge_types:
              request.graph_edge_types,
          });
        }

        try {
          const response =
            await executeAdaptiveRAG(
              payload,
            );

          if (
            requestId !==
            requestIdRef.current
          ) {
            return null;
          }

          setResult(
            response,
          );

          /*
           * Prefer graph context returned by the Adaptive RAG
           * execution because it represents the authoritative
           * graph traversal used for the answer.
           */
          if (
            response.graph
          ) {
            setGraphContext(
              response.graph,
            );
          }

          return response;
        } catch (err) {
          if (
            requestId !==
            requestIdRef.current
          ) {
            return null;
          }

          const message =
            err instanceof Error
              ? err.message
              : "Adaptive RAG execution failed.";

          setError(message);

          setResult(null);

          return null;
        } finally {
          if (
            requestId ===
            requestIdRef.current
          ) {
            setLoading(false);
          }
        }
      },
      [
        autoLoadGraphContext,
        initialStrategy,
        loadGraphContext,
      ],
    );

  /* ------------------------------------------------------------------------ */
  /* Reset                                                                    */
  /* ------------------------------------------------------------------------ */

  const reset =
    useCallback(() => {
      requestIdRef.current += 1;

      graphRequestIdRef.current += 1;

      setResult(null);

      setGraphContext(
        null,
      );

      setError(null);

      setGraphError(null);

      setLoading(false);

      setLoadingGraph(false);
    }, []);

  /* ------------------------------------------------------------------------ */
  /* Automatic Strategy Loading                                               */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (!autoLoadStrategies) {
      return;
    }

    void loadStrategies();
  }, [
    autoLoadStrategies,
    loadStrategies,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Return                                                                   */
  /* ------------------------------------------------------------------------ */

  return {
    result,

    strategies,

    graphContext,

    loading,

    loadingStrategies,

    loadingGraph,

    error,

    graphError,

    execute,

    loadStrategies,

    loadGraphContext,

    reset,
  };
}

export default useAdaptiveRAG;