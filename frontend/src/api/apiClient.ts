/**
 * EcoTrack API Client
 * Manages JWT storage, refresh cycle, headers, and standard fetch wrappers.
 */

const BASE_URL = 'http://127.0.0.1:8000/api/v1';

export interface TokenResponse {
  access: string;
  refresh: string;
}

class ApiClient {
  private accessToken: string | null = localStorage.getItem('access_token');
  private refreshToken: string | null = localStorage.getItem('refresh_token');

  getTokens() {
    return { accessToken: this.accessToken, refreshToken: this.refreshToken };
  }

  setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    
    // Setup headers
    const headers = new Headers(options.headers || {});
    if (this.accessToken) {
      headers.set('Authorization', `Bearer ${this.accessToken}`);
    }
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    let response = await fetch(url, config);

    // Handle token expiration & auto refresh
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.tryRefresh();
      if (refreshed) {
        // Retry original request with new token
        headers.set('Authorization', `Bearer ${this.accessToken}`);
        response = await fetch(url, config);
      } else {
        this.clearTokens();
        window.dispatchEvent(new Event('auth-expired'));
        throw new Error('Session expired');
      }
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { error: { message: 'Network response was not OK' } };
      }
      throw errorData;
    }

    // Handlers for empty / no-content responses (like logout)
    if (response.status === 204) {
      return {} as T;
    }

    return response.json() as Promise<T>;
  }

  private async tryRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${BASE_URL}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: this.refreshToken }),
      });

      if (response.ok) {
        const data: { access: string; refresh?: string } = await response.json();
        this.accessToken = data.access;
        localStorage.setItem('access_token', data.access);
        if (data.refresh) {
          this.refreshToken = data.refresh;
          localStorage.setItem('refresh_token', data.refresh);
        }
        return true;
      }
    } catch (err) {
      console.error('Error refreshing token', err);
    }
    return false;
  }
}

export const apiClient = new ApiClient();
