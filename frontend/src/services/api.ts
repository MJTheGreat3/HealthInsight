/**
 * API Service
 *
 * Centralized API client with authentication, error handling, and retry logic
 */

import { User } from "firebase/auth";

export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = "/api/v1") {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  /**
   * Set authentication token for all requests
   */
  setAuthToken(token: string) {
    this.defaultHeaders["Authorization"] = `Bearer ${token}`;
  }

  /**
   * Remove authentication token
   */
  clearAuthToken() {
    delete this.defaultHeaders["Authorization"];
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = 2
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await this.parseErrorResponse(response);
        throw new ApiError(
          errorData.message,
          response.status,
          errorData.code,
          errorData.details
        );
      }

      // Handle empty responses
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      } else {
        return {} as T;
      }
    } catch (error) {
      // Retry on network errors
      if (retries > 0 && this.isRetryableError(error)) {
        await this.delay(1000 * (3 - retries)); // Exponential backoff
        return this.request<T>(endpoint, options, retries - 1);
      }

      throw error;
    }
  }

  /**
   * Parse error response from API
   */
  private async parseErrorResponse(
    response: Response
  ): Promise<{ message: string; code?: string; details?: any }> {
    try {
      const errorData = await response.json();
      return {
        message: errorData.detail || errorData.message || "An error occurred",
        code: errorData.code,
        details: errorData.details,
      };
    } catch {
      return {
        message: `HTTP ${response.status}: ${response.statusText}`,
      };
    }
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any): boolean {
    // Retry on network errors or 5xx server errors
    return (
      error instanceof TypeError || // Network error
      (error instanceof ApiError && error.status >= 500)
    );
  }

  /**
   * Delay utility for retries
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // HTTP Methods
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = params
      ? `${endpoint}?${new URLSearchParams(params)}`
      : endpoint;
    return this.request<T>(url, { method: "GET" });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const body = data instanceof FormData ? data : JSON.stringify(data);
    const headers =
      data instanceof FormData ? {} : { "Content-Type": "application/json" };

    return this.request<T>(endpoint, {
      method: "POST",
      body,
      headers,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// API Error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// API Service functions
export const apiService = {
  // Authentication
  auth: {
    register: (data: { role: string; name?: string }) =>
      apiClient.post("/auth/register", data),

    login: () => apiClient.post("/auth/login"),

    logout: () => apiClient.post("/auth/logout"),

    getMe: () => apiClient.get("/auth/me"),

    verify: () => apiClient.get("/auth/verify"),
  },

  // Reports
  reports: {
    upload: (file: File, patientId: string) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("patient_id", patientId);
      return apiClient.post("/reports/upload", formData);
    },

    getStatus: (reportId: string) =>
      apiClient.get(`/reports/status/${reportId}`),

    getReport: (reportId: string) => apiClient.get(`/reports/${reportId}`),

    getReports: (skip: number = 0, limit: number = 50) =>
      apiClient.get("/reports", { skip, limit }),

    deleteReport: (reportId: string) =>
      apiClient.delete(`/reports/${reportId}`),

    generateAnalysis: (reportId: string, includeProfile: boolean = true) =>
      apiClient.post(`/reports/${reportId}/analyze`, {
        report_id: reportId,
        include_profile: includeProfile,
      }),

    getAnalysis: (reportId: string) =>
      apiClient.get(`/reports/${reportId}/analysis`),

    generateTrendAnalysis: (trackedMetrics: string[], maxReports: number = 5) =>
      apiClient.post("/reports/trends/analyze", {
        tracked_metrics: trackedMetrics,
        max_reports: maxReports,
      }),
  },

  // Tracked Metrics
  metrics: {
    getTrackedMetrics: () => apiClient.get("/metrics/tracked"),

    addTrackedMetric: (metricName: string) =>
      apiClient.post("/metrics/tracked", { metric_name: metricName }),

    removeTrackedMetric: (metricName: string) =>
      apiClient.delete(`/metrics/tracked/${encodeURIComponent(metricName)}`),

    getMetricHistory: (metricName: string, limit: number = 10) =>
      apiClient.get(`/metrics/history/${encodeURIComponent(metricName)}`, {
        limit,
      }),
  },

  // Search
  search: {
    searchReports: (query: string, filters?: Record<string, any>) =>
      apiClient.get("/search/reports", { query, ...filters }),

    searchPatients: (query: string, filters?: Record<string, any>) =>
      apiClient.get("/search/patients", { query, ...filters }),
  },

  // Chat
  chat: {
    getChatHistory: () => apiClient.get("/chat/history"),

    clearChatHistory: () => apiClient.delete("/chat/history"),
  },

  // Real-time
  realtime: {
    getConnectionStatus: () => apiClient.get("/realtime/status"),
  },
};

// Hook for API authentication
export const useApiAuth = () => {
  const setToken = async (user: User | null) => {
    if (user) {
      const token = await user.getIdToken();
      apiClient.setAuthToken(token);
    } else {
      apiClient.clearAuthToken();
    }
  };

  return { setToken };
};

export default apiService;
