/**
 * Research API client.
 *
 * Responsible only for communicating with the FastAPI research backend.
 *
 * Canonical backend endpoint:
 *
 *     POST /api/v1/research
 *
 * Request:
 *
 *     ResearchRequest
 *
 * Response:
 *
 *     ResearchResponse
 */

import type {
  ResearchRequest,
  ResearchResponse,
} from "./types";


/* ========================================================================== */
/* API configuration                                                          */
/* ========================================================================== */

/**
 * Supported environment variable formats:
 *
 *     NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
 *
 * OR:
 *
 *     NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
 *
 * Both are normalized to:
 *
 *     http://127.0.0.1:8000/api/v1
 */

const RAW_API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


/**
 * Remove trailing slashes.
 */
const NORMALIZED_API_URL =
  RAW_API_URL.replace(/\/+$/, "");


/**
 * Remove /api/v1 if it is already included.
 *
 * This prevents:
 *
 *     /api/v1/api/v1/research
 */
const API_BASE_URL =
  NORMALIZED_API_URL.replace(
    /\/api\/v1$/,
    "",
  );


/**
 * Canonical API v1 URL.
 */
const API_V1_BASE_URL =
  `${API_BASE_URL}/api/v1`;


/**
 * Canonical research endpoint.
 */
const RESEARCH_BASE_URL =
  `${API_V1_BASE_URL}/research`;


/* ========================================================================== */
/* Authentication                                                             */
/* ========================================================================== */

/**
 * Access-token key used by the current AuthProvider.
 */
const TOKEN_KEY =
  "orion_access_token";


/**
 * Get the JWT access token from localStorage.
 *
 * Returns null when:
 *
 * - running during SSR
 * - localStorage is unavailable
 * - no token exists
 * - token is empty
 */
function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const token =
      window.localStorage.getItem(
        TOKEN_KEY,
      );

    if (!token) {
      return null;
    }

    const trimmedToken =
      token.trim();

    return trimmedToken || null;
  } catch (error) {
    console.error(
      "[Research API] Unable to access localStorage:",
      error,
    );

    return null;
  }
}


/* ========================================================================== */
/* Error types                                                                */
/* ========================================================================== */

/**
 * Structured API error.
 *
 * Keeps:
 *
 * - HTTP status
 * - status text
 * - request URL
 * - backend response body
 *
 * available to the caller.
 */
export class ResearchApiError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly url: string;
  readonly data: unknown;

  constructor(
    message: string,
    options: {
      status: number;
      statusText: string;
      url: string;
      data?: unknown;
    },
  ) {
    super(message);

    this.name = "ResearchApiError";
    this.status = options.status;
    this.statusText = options.statusText;
    this.url = options.url;
    this.data = options.data;

    Object.setPrototypeOf(
      this,
      ResearchApiError.prototype,
    );
  }
}


/* ========================================================================== */
/* Error parsing                                                              */
/* ========================================================================== */

/**
 * Safely read a response body.
 *
 * Handles:
 *
 * - JSON
 * - plain text
 * - HTML
 * - empty responses
 */
async function readResponseBody(
  response: Response,
): Promise<unknown> {
  const contentType =
    response.headers.get(
      "content-type",
    ) ?? "";


  try {
    if (
      contentType
        .toLowerCase()
        .includes("application/json")
    ) {
      return await response.json();
    }

    const text =
      await response.text();

    return text || null;
  } catch {
    return null;
  }
}


/**
 * Extract a useful message from an API response.
 */
function getErrorMessageFromData(
  data: unknown,
  response: Response,
): string {
  const fallback =
    `Research API request failed: ` +
    `${response.status} ${response.statusText}`;


  if (
    typeof data === "string" &&
    data.trim()
  ) {
    return data.trim();
  }


  if (
    typeof data !== "object" ||
    data === null
  ) {
    return fallback;
  }


  /* ------------------------------------------------------------------------ */
  /* FastAPI detail                                                            */
  /* ------------------------------------------------------------------------ */

  if ("detail" in data) {
    const detail =
      (
        data as {
          detail?: unknown;
        }
      ).detail;


    if (typeof detail === "string") {
      return detail;
    }


    if (Array.isArray(detail)) {
      const messages =
        detail
          .map((item) => {
            if (
              typeof item === "object" &&
              item !== null &&
              "msg" in item
            ) {
              const message =
                (
                  item as {
                    msg?: unknown;
                  }
                ).msg;

              if (
                typeof message === "string"
              ) {
                return message;
              }
            }

            return String(item);
          })
          .filter(Boolean);


      if (messages.length > 0) {
        return messages.join(", ");
      }
    }


    if (
      detail !== undefined &&
      detail !== null
    ) {
      return String(detail);
    }
  }


  /* ------------------------------------------------------------------------ */
  /* Generic message                                                           */
  /* ------------------------------------------------------------------------ */

  if ("message" in data) {
    const message =
      (
        data as {
          message?: unknown;
        }
      ).message;


    if (
      typeof message === "string" &&
      message.trim()
    ) {
      return message;
    }
  }


  /* ------------------------------------------------------------------------ */
  /* Generic error                                                             */
  /* ------------------------------------------------------------------------ */

  if ("error" in data) {
    const error =
      (
        data as {
          error?: unknown;
        }
      ).error;


    if (typeof error === "string") {
      return error;
    }


    if (
      typeof error === "object" &&
      error !== null &&
      "message" in error
    ) {
      const message =
        (
          error as {
            message?: unknown;
          }
        ).message;


      if (
        typeof message === "string" &&
        message.trim()
      ) {
        return message;
      }
    }
  }


  return fallback;
}


/**
 * Extract a useful error message from a non-2xx response.
 */
async function extractErrorMessage(
  response: Response,
): Promise<{
  message: string;
  data: unknown;
}> {
  const data =
    await readResponseBody(
      response,
    );


  return {
    message:
      getErrorMessageFromData(
        data,
        response,
      ),
    data,
  };
}


/* ========================================================================== */
/* Development logging                                                        */
/* ========================================================================== */

/**
 * Log outgoing requests during development.
 */
function logRequest(
  method: string,
  url: string,
  authenticated: boolean,
): void {
  if (
    process.env.NODE_ENV !==
    "development"
  ) {
    return;
  }


  console.debug(
    "[Research API] Request:",
    {
      method,
      url,
      authenticated,
      frontendOrigin:
        typeof window !== "undefined"
          ? window.location.origin
          : undefined,
    },
  );
}


/**
 * Log successful HTTP responses during development.
 */
function logResponse(
  response: Response,
): void {
  if (
    process.env.NODE_ENV !==
    "development"
  ) {
    return;
  }


  console.debug(
    "[Research API] Response:",
    {
      status:
        response.status,
      statusText:
        response.statusText,
      url:
        response.url,
      ok:
        response.ok,
    },
  );
}


/* ========================================================================== */
/* Generic request                                                            */
/* ========================================================================== */

/**
 * Generic authenticated request helper.
 *
 * The path is relative to:
 *
 *     /api/v1/research
 *
 * Examples:
 *
 *     request("")
 *     request("/history")
 *     request("/123")
 */
async function request<T>(
  path = "",
  options: RequestInit = {},
): Promise<T> {
  const token =
    getAccessToken();


  /* ------------------------------------------------------------------------ */
  /* Normalize path                                                            */
  /* ------------------------------------------------------------------------ */

  const normalizedPath =
    path
      ? path.startsWith("/")
        ? path
        : `/${path}`
      : "";


  /* ------------------------------------------------------------------------ */
  /* Build URL                                                                 */
  /* ------------------------------------------------------------------------ */

  const url =
    `${RESEARCH_BASE_URL}${normalizedPath}`;


  /* ------------------------------------------------------------------------ */
  /* Headers                                                                   */
  /* ------------------------------------------------------------------------ */

  const headers =
    new Headers(
      options.headers,
    );


  /**
   * Automatically send JSON content type when a body exists.
   */
  if (
    options.body &&
    !headers.has(
      "Content-Type",
    )
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }


  /**
   * Research API returns JSON.
   */
  if (
    !headers.has(
      "Accept",
    )
  ) {
    headers.set(
      "Accept",
      "application/json",
    );
  }


  /**
   * JWT authentication.
   *
   * This is intentionally handled through the Authorization header.
   */
  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Development logging                                                      */
  /* ------------------------------------------------------------------------ */

  logRequest(
    options.method ?? "GET",
    url,
    Boolean(token),
  );


  /* ------------------------------------------------------------------------ */
  /* Fetch                                                                     */
  /* ------------------------------------------------------------------------ */

  let response: Response;


  try {
    response =
      await fetch(
        url,
        {
          ...options,

          headers,

          /**
           * Authentication is handled explicitly through:
           *
           *     Authorization: Bearer <token>
           *
           * The frontend and backend are different origins during
           * local development:
           *
           *     localhost:3000
           *     127.0.0.1:8000
           *
           * No authentication cookies are required.
           */
          credentials:
            "omit",

          /**
           * Research requests should never use a stale browser cache.
           */
          cache:
            "no-store",

          /**
           * Explicitly use CORS mode for the cross-origin FastAPI request.
           */
          mode:
            "cors",
        },
      );
  } catch (error) {
    /**
     * IMPORTANT:
     *
     * This block only executes when fetch cannot obtain an HTTP response.
     *
     * Examples:
     *
     * - backend is not running
     * - connection refused
     * - CORS/network failure
     * - browser extension interference
     * - browser connectivity problem
     *
     * HTTP 400/401/404/422/500 responses do NOT reach this block.
     */

    const message =
      error instanceof Error
        ? error.message
        : String(error);


    const name =
      error instanceof Error
        ? error.name
        : "UnknownError";


    const stack =
      error instanceof Error
        ? error.stack
        : undefined;


    console.error(
      "[Research API] Network error:",
      {
        url,
        name,
        message,
        stack,
        error,

        frontendOrigin:
          typeof window !== "undefined"
            ? window.location.origin
            : undefined,

        backendOrigin:
          API_BASE_URL,
      },
    );


    throw new Error(
      "Unable to reach the research backend. " +
      `Request URL: ${url}. ` +
      `Frontend origin: ${
        typeof window !== "undefined"
          ? window.location.origin
          : "unknown"
      }. ` +
      `Original error: ${message}`,
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Response logging                                                          */
  /* ------------------------------------------------------------------------ */

  logResponse(
    response,
  );


  /* ------------------------------------------------------------------------ */
  /* HTTP errors                                                               */
  /* ------------------------------------------------------------------------ */

  if (!response.ok) {
    const {
      message,
      data,
    } =
      await extractErrorMessage(
        response,
      );


    /* ---------------------------------------------------------------------- */
    /* Authentication failure                                                 */
    /* ---------------------------------------------------------------------- */

    if (
      response.status ===
      401
    ) {
      console.error(
        "[Research API] Authentication failed.",
        {
          url,
          status:
            response.status,
          message,
          hasToken:
            Boolean(token),
        },
      );
    }


    /* ---------------------------------------------------------------------- */
    /* Forbidden                                                               */
    /* ---------------------------------------------------------------------- */

    if (
      response.status ===
      403
    ) {
      console.error(
        "[Research API] Access forbidden.",
        {
          url,
          status:
            response.status,
          message,
        },
      );
    }


    /* ---------------------------------------------------------------------- */
    /* Not found                                                               */
    /* ---------------------------------------------------------------------- */

    if (
      response.status ===
      404
    ) {
      console.error(
        "[Research API] Endpoint not found.",
        {
          url,
          status:
            response.status,
          message,
        },
      );
    }


    /* ---------------------------------------------------------------------- */
    /* Bad request                                                             */
    /* ---------------------------------------------------------------------- */

    if (
      response.status ===
      400
    ) {
      console.error(
        "[Research API] Bad request.",
        {
          url,
          status:
            response.status,
          message,
          data,
        },
      );
    }


    /* ---------------------------------------------------------------------- */
    /* Validation error                                                        */
    /* ---------------------------------------------------------------------- */

    if (
      response.status ===
      422
    ) {
      console.error(
        "[Research API] Validation error.",
        {
          url,
          status:
            response.status,
          message,
          data,
        },
      );
    }


    /* ---------------------------------------------------------------------- */
    /* Backend failure                                                         */
    /* ---------------------------------------------------------------------- */

    if (
      response.status >=
      500
    ) {
      console.error(
        "[Research API] Backend error.",
        {
          url,
          status:
            response.status,
          statusText:
            response.statusText,
          message,
          data,
        },
      );
    }


    throw new ResearchApiError(
      message,
      {
        status:
          response.status,
        statusText:
          response.statusText,
        url,
        data,
      },
    );
  }


  /* ------------------------------------------------------------------------ */
  /* No content                                                               */
  /* ------------------------------------------------------------------------ */

  if (
    response.status ===
    204
  ) {
    return undefined as T;
  }


  /* ------------------------------------------------------------------------ */
  /* JSON response                                                             */
  /* ------------------------------------------------------------------------ */

  try {
    return (
      await response.json()
    ) as T;
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : String(error);


    console.error(
      "[Research API] Invalid JSON response:",
      {
        url,
        status:
          response.status,
        message,
        error,
      },
    );


    throw new Error(
      "The research backend returned " +
      "an invalid JSON response.",
    );
  }
}


/* ========================================================================== */
/* Start research                                                             */
/* ========================================================================== */

/**
 * Start a research execution.
 *
 * Backend:
 *
 *     POST /api/v1/research
 *
 * Request:
 *
 *     ResearchRequest
 *
 * Response:
 *
 *     ResearchResponse
 */
export async function startResearch(
  payload: ResearchRequest,
): Promise<ResearchResponse> {
  /* ------------------------------------------------------------------------ */
  /* Validate payload                                                          */
  /* ------------------------------------------------------------------------ */

  const question =
    payload.question?.trim();


  if (
    !question ||
    question.length < 3
  ) {
    throw new Error(
      "A research question is required.",
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Normalize payload                                                         */
  /* ------------------------------------------------------------------------ */

  const normalizedPayload:
    ResearchRequest = {
      ...payload,
      question,
    };


  /* ------------------------------------------------------------------------ */
  /* Development logging                                                      */
  /* ------------------------------------------------------------------------ */

  if (
    process.env.NODE_ENV ===
    "development"
  ) {
    console.debug(
      "[Research API] Starting research:",
      {
        endpoint:
          RESEARCH_BASE_URL,

        question,

        depth:
          normalizedPayload.depth,

        include_papers:
          normalizedPayload.include_papers,

        include_github:
          normalizedPayload.include_github,

        include_docs:
          normalizedPayload.include_docs,

        collection_id:
          "collection_id" in
          normalizedPayload
            ? normalizedPayload.collection_id
            : undefined,
      },
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Execute request                                                          */
  /* ------------------------------------------------------------------------ */

  return request<ResearchResponse>(
    "",
    {
      method: "POST",

      body: JSON.stringify(
        normalizedPayload,
      ),
    },
  );
}


/* ========================================================================== */
/* Execute research alias                                                     */
/* ========================================================================== */

/**
 * Backwards-compatible alias.
 *
 * Both functions call:
 *
 *     POST /api/v1/research
 */
export async function executeResearch(
  payload: ResearchRequest,
): Promise<ResearchResponse> {
  return startResearch(
    payload,
  );
}


/* ========================================================================== */
/* Default API object                                                         */
/* ========================================================================== */

const researchApi = {
  startResearch,
  executeResearch,
};


export default researchApi;