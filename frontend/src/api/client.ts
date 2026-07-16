import { API_URL } from '../config'
import type { TokenResponse, User } from '../types'

const TOKEN_KEY = 'athena_access_token'
const REFRESH_KEY = 'athena_refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setTokens(tokens: TokenResponse): void {
  localStorage.setItem(TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY)

  if (!refresh) {
    return null
  }

  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  })

  if (!response.ok) {
    clearTokens()
    return null
  }

  const tokens = (await response.json()) as TokenResponse
  setTokens(tokens)
  return tokens.access_token
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers)

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  let token = getAccessToken()

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401 && localStorage.getItem(REFRESH_KEY)) {
    token = await refreshAccessToken()

    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
      response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
      })
    }
  }

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    throw new Error('Login failed')
  }

  const tokens = (await response.json()) as TokenResponse
  setTokens(tokens)
  return tokens
}

export async function register(payload: {
  username: string
  email: string
  full_name: string
  password: string
}): Promise<User> {
  return apiFetch<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getMe(): Promise<User> {
  return apiFetch<User>('/auth/me')
}

export async function getHealth(): Promise<Record<string, string>> {
  return apiFetch('/health')
}
