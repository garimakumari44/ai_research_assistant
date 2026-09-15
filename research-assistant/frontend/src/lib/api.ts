
export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
  detail?: string;
  message?: string;
  code?: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;
  data?: unknown;

  constructor(
    message: string,
    options: {
      status: number;
      code?: string;
      details?: unknown;
      data?: unknown;
    },
  ) {
    super(message);

    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details;
    this.data = options.data;

    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/* -------------------------------------------------------------------------- */
/* API URL                                                                    */
/* -------------------------------------------------------------------------- */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1";

export function getApiUrl(): string {
  return API_BASE_URL;
}

/* -------------------------------------------------------------------------- */
/* Token Storage                                                              */
/* -------------------------------------------------------------------------- */

const ACCESS_TOKEN_KEY = "orion_access_token";
const REFRESH_TOKEN_KEY = "orion_refresh_token";
const USER_KEY = "orion_user";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    return token?.trim() || null;
  } catch {
    return null;
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const token = localStorage.getItem(REFRESH_TOKEN_KEY);
    return token?.trim() || null;
  } catch {
    return null;
  }
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (!token?.trim()) {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      return;
    }

    localStorage.setItem(ACCESS_TOKEN_KEY, token.trim());
  } catch {
    // Ignore localStorage failures.
  }
}

export function setRefreshToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (!token?.trim()) {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      return;
    }

    localStorage.setItem(REFRESH_TOKEN_KEY, token.trim());
  } catch {
    // Ignore localStorage failures.
  }
}

export function saveTokens(
  accessToken: string,
  refreshToken: string,
): void {
  setAccessToken(accessToken);
  setRefreshToken(refreshToken);
}

export function saveUser(user: unknown): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    // Ignore localStorage failures.
  }
}

export function getUser<T = unknown>(): T | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const user = localStorage.getItem(USER_KEY);

    if (!user) {
      return null;
    }

    return JSON.parse(user) as T;
  } catch {
    return null;
  }
}

export function clearAuthTokens(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // Ignore localStorage failures.
  }
}

export function clearAuth(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  } catch {
    // Ignore localStorage failures.
  }
}

export function logoutAndRedirect(): void {
  if (typeof window === "undefined") {
    return;
  }

  clearAuth();

  if (window.location.pathname !== "/login") {
    window.location.replace("/login");
  }
}

/* -------------------------------------------------------------------------- */
/* Authentication                                                             */
/* -------------------------------------------------------------------------- */

export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    console.warn(
      "[auth] Cannot refresh access token: no refresh token found.",
    );

    return null;
  }

  const url = `${API_BASE_URL}/auth/refresh`;

  try {
    const response = await fetch(url, {
      method: "POST",

      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },

      credentials: "include",

      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    const payload = await parseResponseBody(response);

    if (!response.ok) {
      console.warn("[auth] Token refresh failed.", {
        status: response.status,
        url,
      });

      return null;
    }

    if (!payload || typeof payload !== "object") {
      console.warn("[auth] Invalid token refresh response.");
      return null;
    }

    const data = payload as {
      access_token?: string;
      refresh_token?: string;
      token_type?: string;
    };

    if (
      typeof data.access_token !== "string" ||
      !data.access_token.trim()
    ) {
      console.warn(
        "[auth] Refresh response did not contain access_token.",
      );

      return null;
    }

    setAccessToken(data.access_token);

    if (
      typeof data.refresh_token === "string" &&
      data.refresh_token.trim()
    ) {
      setRefreshToken(data.refresh_token);
    }

    console.log("[auth] Access token refreshed successfully.");

    return data.access_token;
  } catch (error) {
    console.warn("[auth] Token refresh network error.", error);
    return null;
  }
}

/* -------------------------------------------------------------------------- */
/* Error Handling                                                             */
/* -------------------------------------------------------------------------- */

function getErrorMessage(
  payload: unknown,
  fallback: string,
): string {
  if (
    typeof payload === "string" &&
    payload.trim()
  ) {
    return payload;
  }

  if (
    payload &&
    typeof payload === "object"
  ) {
    const value = payload as ApiErrorPayload;

    if (
      typeof value.error?.message === "string"
    ) {
      return value.error.message;
    }

    if (
      typeof value.detail === "string"
    ) {
      return value.detail;
    }

    if (
      typeof value.message === "string"
    ) {
      return value.message;
    }
  }

  return fallback;
}

function getErrorCode(
  payload: unknown,
): string | undefined {
  if (
    !payload ||
    typeof payload !== "object"
  ) {
    return undefined;
  }

  const value = payload as ApiErrorPayload;

  if (
    typeof value.error?.code === "string"
  ) {
    return value.error.code;
  }

  if (
    typeof value.code === "string"
  ) {
    return value.code;
  }

  return undefined;
}

async function parseResponseBody(
  response: Response,
): Promise<unknown> {
  const contentType =
    response.headers.get("content-type") ?? "";

  if (
    contentType.includes("application/json")
  ) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  try {
    const text = await response.text();
    return text || null;
  } catch {
    return null;
  }
}

/* -------------------------------------------------------------------------- */
/* Authenticated Headers                                                      */
/* -------------------------------------------------------------------------- */

function getAuthHeaders(
  headers?: HeadersInit,
): Headers {
  const result = new Headers(headers);

  const accessToken = getAccessToken();

  if (
    accessToken &&
    !result.has("Authorization")
  ) {
    result.set(
      "Authorization",
      `Bearer ${accessToken}`,
    );
  }

  if (!result.has("Accept")) {
    result.set(
      "Accept",
      "application/json",
    );
  }

  return result;
}

/* -------------------------------------------------------------------------- */
/* Request Helpers                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Only JSON/string bodies should automatically receive
 * application/json.
 *
 * FormData MUST NOT receive a manually assigned Content-Type,
 * because the browser must generate:
 *
 * multipart/form-data; boundary=...
 */
function prepareHeaders(
  headers?: HeadersInit,
  init?: RequestInit,
): Headers {
  const result = getAuthHeaders(headers);

  const body = init?.body;

  const isFormData =
    typeof FormData !== "undefined" &&
    body instanceof FormData;

  const isURLSearchParams =
    typeof URLSearchParams !== "undefined" &&
    body instanceof URLSearchParams;

  const hasBody =
    body !== undefined &&
    body !== null;

  if (
    hasBody &&
    !isFormData &&
    !isURLSearchParams &&
    !result.has("Content-Type")
  ) {
    result.set(
      "Content-Type",
      "application/json",
    );
  }

  return result;
}

/* -------------------------------------------------------------------------- */
/* Request Execution                                                          */
/* -------------------------------------------------------------------------- */

async function executeRequest<T>(
  path: string,
  init: RequestInit = {},
  options: {
    retryOn401?: boolean;
  } = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const retryOn401 =
    options.retryOn401 ?? true;

  const headers = prepareHeaders(
    init.headers,
    init,
  );

  if (typeof window !== "undefined") {
    console.debug(
      "[browser] API REQUEST",
      {
        method: init.method ?? "GET",
        url,
        hasAccessToken: Boolean(
          getAccessToken(),
        ),
        isFormData:
          typeof FormData !== "undefined" &&
          init.body instanceof FormData,
      },
    );
  }

  try {
    const response = await fetch(url, {
      ...init,
      headers,
      credentials: "include",
    });

    const payload =
      await parseResponseBody(response);

    /* ---------------------------------------------------------------------- */
    /* Automatic token refresh                                                */
    /* ---------------------------------------------------------------------- */

    if (
      response.status === 401 &&
      retryOn401
    ) {
      console.warn(
        "[auth] API request returned 401. Attempting token refresh.",
        {
          method: init.method ?? "GET",
          url,
          hasRefreshToken: Boolean(
            getRefreshToken(),
          ),
        },
      );

      const newAccessToken =
        await refreshAccessToken();

      if (newAccessToken) {
        const retryHeaders =
          prepareHeaders(
            init.headers,
            init,
          );

        retryHeaders.set(
          "Authorization",
          `Bearer ${newAccessToken}`,
        );

        const retryResponse =
          await fetch(url, {
            ...init,
            headers: retryHeaders,
            credentials: "include",
          });

        const retryPayload =
          await parseResponseBody(
            retryResponse,
          );

        if (retryResponse.ok) {
          if (
            retryResponse.status === 204
          ) {
            return undefined as T;
          }

          return retryPayload as T;
        }

        if (
          retryResponse.status === 401
        ) {
          console.warn(
            "[auth] Refreshed access token was rejected. Logging out.",
          );

          logoutAndRedirect();

          throw new ApiError(
            "Your session has expired. Please log in again.",
            {
              status: 401,
              data: retryPayload,
            },
          );
        }

        const retryMessage =
          getErrorMessage(
            retryPayload,
            `Request failed with status ${retryResponse.status}`,
          );

        throw new ApiError(
          retryMessage,
          {
            status:
              retryResponse.status,

            code:
              getErrorCode(
                retryPayload,
              ),

            data:
              retryPayload,

            details:
              retryPayload &&
              typeof retryPayload ===
                "object"
                ? (
                    retryPayload as ApiErrorPayload
                  ).error?.details
                : undefined,
          },
        );
      }

      console.warn(
        "[auth] Refresh token is invalid or expired. Logging out.",
      );

      logoutAndRedirect();

      throw new ApiError(
        "Your session has expired. Please log in again.",
        {
          status: 401,
          data: payload,
        },
      );
    }

    /* ---------------------------------------------------------------------- */
    /* Normal error handling                                                  */
    /* ---------------------------------------------------------------------- */

    if (!response.ok) {
      const message =
        getErrorMessage(
          payload,
          `Request failed with status ${response.status}`,
        );

      const error =
        new ApiError(
          message,
          {
            status:
              response.status,

            code:
              getErrorCode(
                payload,
              ),

            data:
              payload,

            details:
              payload &&
              typeof payload ===
                "object"
                ? (
                    payload as ApiErrorPayload
                  ).error?.details
                : undefined,
          },
        );

      console.error(
        "[browser] API ERROR",
        {
          method:
            init.method ?? "GET",

          url,

          status:
            response.status,

          code:
            error.code,

          message:
            error.message,

          response:
            payload,
        },
      );

      throw error;
    }

    /* ---------------------------------------------------------------------- */
    /* Successful response                                                    */
    /* ---------------------------------------------------------------------- */

    if (
      response.status === 204
    ) {
      return undefined as T;
    }

    return payload as T;
  } catch (error) {
    if (
      error instanceof ApiError
    ) {
      throw error;
    }

    const normalized =
      error instanceof Error
        ? error
        : new Error(String(error));

    console.error(
      "[browser] API NETWORK ERROR",
      {
        method:
          init.method ?? "GET",

        url,

        name:
          normalized.name,

        message:
          normalized.message,

        stack:
          normalized.stack,
      },
    );

    throw normalized;
  }
}

/* -------------------------------------------------------------------------- */
/* Generic API                                                                */
/* -------------------------------------------------------------------------- */

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  return executeRequest<T>(
    path,
    init,
  );
}

export async function apiGet<T>(
  path: string,
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "GET",
    },
  );
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "POST",

      body:
        body === undefined
          ? undefined
          : JSON.stringify(body),
    },
  );
}

export async function apiPatch<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "PATCH",

      body:
        body === undefined
          ? undefined
          : JSON.stringify(body),
    },
  );
}

export async function apiDelete<T>(
  path: string,
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "DELETE",
    },
  );
}

