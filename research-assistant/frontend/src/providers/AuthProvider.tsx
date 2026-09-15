"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useRouter } from "next/navigation";

import {
  apiGet,
  apiPost,
  clearAuthTokens,
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
} from "@/lib/api";

/* ========================================================================== */
/* Types                                                                      */
/* ========================================================================== */

export interface User {
  id: number;
  email: string;
  full_name: string | null;
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;

  login(email: string, password: string): Promise<void>;
  register(data: RegisterData): Promise<void>;
  logout(): void;
}

/* ========================================================================== */
/* Context                                                                    */
/* ========================================================================== */

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/* ========================================================================== */
/* Constants                                                                  */
/* ========================================================================== */

const USER_KEY = "orion_user";

/* ========================================================================== */
/* Storage Helpers                                                            */
/* ========================================================================== */

function saveUser(user: User): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (error) {
    console.warn("[auth] Failed to persist user:", error);
  }
}

function clearUser(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.removeItem(USER_KEY);
  } catch (error) {
    console.warn("[auth] Failed to clear stored user:", error);
  }
}

/* ========================================================================== */
/* Error Helpers                                                              */
/* ========================================================================== */

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    return error.message || fallback;
  }

  if (typeof error === "object" && error !== null) {
    const candidate = error as {
      message?: unknown;
      detail?: unknown;
      error?: unknown;
    };

    if (
      typeof candidate.message === "string" &&
      candidate.message.trim()
    ) {
      return candidate.message;
    }

    if (
      typeof candidate.detail === "string" &&
      candidate.detail.trim()
    ) {
      return candidate.detail;
    }

    if (
      typeof candidate.error === "string" &&
      candidate.error.trim()
    ) {
      return candidate.error;
    }
  }

  return fallback;
}

/* ========================================================================== */
/* Auth Provider                                                              */
/* ========================================================================== */

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);

  const [token, setToken] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);

  /* ------------------------------------------------------------------------ */
  /* Load Authenticated User                                                  */
  /* ------------------------------------------------------------------------ */

  const loadCurrentUser = useCallback(
    async (): Promise<User> => {
      return apiGet<User>("/auth/me");
    },
    [],
  );

  /* ------------------------------------------------------------------------ */
  /* Restore Session                                                          */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    let mounted = true;

    async function restoreSession(): Promise<void> {
      const storedAccessToken = getAccessToken();
      const storedRefreshToken = getRefreshToken();

      console.debug("[auth] Restoring session", {
        hasAccessToken: Boolean(storedAccessToken),
        hasRefreshToken: Boolean(storedRefreshToken),
      });

      if (!storedAccessToken && !storedRefreshToken) {
        if (mounted) {
          setToken(null);
          setUser(null);
          setLoading(false);
        }

        return;
      }

      try {
        const currentUser = await loadCurrentUser();

        if (!mounted) {
          return;
        }

        const activeToken = getAccessToken();

        setToken(activeToken);
        setUser(currentUser);

        saveUser(currentUser);

        console.debug(
          "[auth] Session restored successfully.",
          {
            hasAccessToken: Boolean(activeToken),
            userId: currentUser.id,
          },
        );
      } catch (error) {
        console.warn(
          "[auth] Unable to restore authentication session:",
          error,
        );

        clearAuthTokens();
        clearUser();

        if (mounted) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      mounted = false;
    };
  }, [loadCurrentUser]);

  /* ------------------------------------------------------------------------ */
  /* Login                                                                    */
  /* ------------------------------------------------------------------------ */

  const login = useCallback(
    async (
      email: string,
      password: string,
    ): Promise<void> => {
      clearAuthTokens();
      clearUser();

      setToken(null);
      setUser(null);

      const normalizedEmail = email.trim().toLowerCase();

      if (!normalizedEmail) {
        throw new Error("Email address is required.");
      }

      if (!password) {
        throw new Error("Password is required.");
      }

      try {
        const response = await apiPost<TokenResponse>(
          "/auth/login",
          {
            email: normalizedEmail,
            password,
          },
        );

        const accessToken =
          typeof response?.access_token === "string"
            ? response.access_token.trim()
            : "";

        const refreshToken =
          typeof response?.refresh_token === "string"
            ? response.refresh_token.trim()
            : "";

        if (!accessToken) {
          throw new Error(
            "Login succeeded but the backend did not return an access token.",
          );
        }

        if (!refreshToken) {
          throw new Error(
            "Login succeeded but the backend did not return a refresh token.",
          );
        }

        setAccessToken(accessToken);
        setRefreshToken(refreshToken);

        const savedAccessToken = getAccessToken();
        const savedRefreshToken = getRefreshToken();

        if (!savedAccessToken || !savedRefreshToken) {
          clearAuthTokens();

          throw new Error(
            "Login succeeded but authentication tokens could not be stored in the browser.",
          );
        }

        setToken(accessToken);

        console.debug("[auth] Login tokens stored", {
          hasAccessToken: Boolean(savedAccessToken),
          hasRefreshToken: Boolean(savedRefreshToken),
        });

        const currentUser = await loadCurrentUser();

        saveUser(currentUser);
        setUser(currentUser);

        console.debug("[auth] Login completed successfully", {
          userId: currentUser.id,
          email: currentUser.email,
        });

        router.replace("/dashboard");
      } catch (error) {
        clearAuthTokens();
        clearUser();

        setToken(null);
        setUser(null);

        const message = getErrorMessage(
          error,
          "Login failed.",
        );

        console.error("[auth] Login failed:", error);

        throw new Error(message);
      }
    },
    [loadCurrentUser, router],
  );

  /* ------------------------------------------------------------------------ */
  /* Register                                                                 */
  /* ------------------------------------------------------------------------ */

  const register = useCallback(
    async (
      data: RegisterData,
    ): Promise<void> => {
      const fullName = data.full_name.trim();

      const email = data.email.trim().toLowerCase();

      const password = data.password;

      if (!fullName) {
        throw new Error("Full name is required.");
      }

      if (!email) {
        throw new Error("Email address is required.");
      }

      if (!password) {
        throw new Error("Password is required.");
      }

      try {
        const result = await apiPost<User | TokenResponse>(
          "/auth/register",
          {
            full_name: fullName,
            email,
            password,
          },
        );

        const possibleTokens =
          result as Partial<TokenResponse>;

        const accessToken =
          typeof possibleTokens?.access_token === "string"
            ? possibleTokens.access_token.trim()
            : "";

        const refreshToken =
          typeof possibleTokens?.refresh_token === "string"
            ? possibleTokens.refresh_token.trim()
            : "";

        if (!accessToken) {
          console.debug(
            "[auth] Registration completed. Backend did not return tokens.",
          );

          router.replace("/");

          return;
        }

        if (!refreshToken) {
          throw new Error(
            "Registration returned an access token but no refresh token.",
          );
        }

        setAccessToken(accessToken);
        setRefreshToken(refreshToken);

        const savedAccessToken = getAccessToken();
        const savedRefreshToken = getRefreshToken();

        if (!savedAccessToken || !savedRefreshToken) {
          clearAuthTokens();

          throw new Error(
            "Registration succeeded but authentication tokens could not be stored in the browser.",
          );
        }

        setToken(accessToken);

        const currentUser = await loadCurrentUser();

        saveUser(currentUser);
        setUser(currentUser);

        console.debug(
          "[auth] Registration completed with automatic authentication.",
          {
            userId: currentUser.id,
          },
        );

        router.replace("/dashboard");
      } catch (error) {
        clearAuthTokens();
        clearUser();

        setToken(null);
        setUser(null);

        const message = getErrorMessage(
          error,
          "Registration failed.",
        );

        console.error(
          "[auth] Registration failed:",
          error,
        );

        throw new Error(message);
      }
    },
    [loadCurrentUser, router],
  );

  /* ------------------------------------------------------------------------ */
  /* Logout                                                                   */
  /* ------------------------------------------------------------------------ */

  const logout = useCallback((): void => {
    console.debug("[auth] Logging out.");

    clearAuthTokens();
    clearUser();

    setToken(null);
    setUser(null);

    router.replace("/");
  }, [router]);

  /* ------------------------------------------------------------------------ */
  /* Context Value                                                            */
  /* ------------------------------------------------------------------------ */

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(token),

      login,
      register,
      logout,
    }),
    [
      user,
      token,
      loading,
      login,
      register,
      logout,
    ],
  );

  /* ------------------------------------------------------------------------ */
  /* Provider                                                                 */
  /* ------------------------------------------------------------------------ */

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/* ========================================================================== */
/* useAuth                                                                    */
/* ========================================================================== */

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}
