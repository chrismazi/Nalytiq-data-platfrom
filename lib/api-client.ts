/**
 * Enhanced API Client with comprehensive error handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network connection failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public errors: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
}

class APIClient {
  private baseURL: string;
  private defaultTimeout: number = 30000; // 30 seconds

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  }

  private async fetchWithTimeout(
    url: string,
    options: RequestConfig = {}
  ): Promise<Response> {
    const { timeout = this.defaultTimeout, ...fetchOptions } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new NetworkError('Request timeout');
      }
      throw new NetworkError('Network request failed');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestConfig = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getAuthToken();

    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    // Add auth token if available and not FormData
    if (token && !(options.body instanceof FormData)) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Add Content-Type for JSON
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await this.fetchWithTimeout(url, {
        ...options,
        headers,
      });

      // Handle different response types
      const contentType = response.headers.get('content-type');
      let data: any;

      if (contentType?.includes('application/json')) {
        data = await response.json();
      } else if (contentType?.includes('text/html')) {
        data = await response.text();
      } else {
        data = await response.text();
      }

      // Handle error responses
      if (!response.ok) {
        if (response.status === 401) {
          // Clear token and redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }
          throw new APIError('Unauthorized', 401, 'UNAUTHORIZED');
        }

        if (response.status === 422) {
          // Validation error
          throw new ValidationError(
            data.detail || 'Validation failed',
            data.errors || {}
          );
        }

        throw new APIError(
          data.error || data.detail || 'Request failed',
          response.status,
          data.code,
          data
        );
      }

      return data as T;
    } catch (error) {
      if (
        error instanceof APIError ||
        error instanceof NetworkError ||
        error instanceof ValidationError
      ) {
        throw error;
      }
      throw new NetworkError('An unexpected error occurred');
    }
  }

  async get<T>(endpoint: string, options?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(
    endpoint: string,
    body?: any,
    options?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  async put<T>(
    endpoint: string,
    body?: any,
    options?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string, options?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  async uploadFile<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    return this.post<T>(endpoint, formData, {
      timeout: 120000, // 2 minutes for large files
    });
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export typed API methods
export const api = {
  client: apiClient,
  
  // Helper method to handle errors consistently
  handleError: (error: unknown): string => {
    if (error instanceof ValidationError) {
      const errorMessages = Object.values(error.errors).flat();
      return errorMessages.join(', ') || 'Validation failed';
    }
    
    if (error instanceof APIError) {
      return error.message;
    }
    
    if (error instanceof NetworkError) {
      return error.message;
    }
    
    if (error instanceof Error) {
      return error.message;
    }
    
    return 'An unexpected error occurred';
  },
};
