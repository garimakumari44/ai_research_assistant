const ACCESS_TOKEN =
  "orion_access_token";

const REFRESH_TOKEN =
  "orion_refresh_token";

const USER =
  "orion_user";

export function saveTokens(
  access: string,
  refresh: string
) {
  localStorage.setItem(
    ACCESS_TOKEN,
    access
  );

  localStorage.setItem(
    REFRESH_TOKEN,
    refresh
  );
}

export function getAccessToken() {
  return localStorage.getItem(
    ACCESS_TOKEN
  );
}

export function getRefreshToken() {
  return localStorage.getItem(
    REFRESH_TOKEN
  );
}

export function saveUser(
  user: unknown
) {
  localStorage.setItem(
    USER,
    JSON.stringify(user)
  );
}

export function getUser<T = unknown>(): T | null {
  const user =
    localStorage.getItem(USER);

  return user
    ? JSON.parse(user)
    : null;
}

export function clearAuth() {
  localStorage.removeItem(
    ACCESS_TOKEN
  );

  localStorage.removeItem(
    REFRESH_TOKEN
  );

  localStorage.removeItem(
    USER
  );
}