import axios from 'axios';

declare const process: {
  env: {
    REACT_APP_API_URL?: string;
  };
};

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API Service
export const apiService = {
  // Health endpoints
  health: {
    check: () => apiClient.get('/health'),
    database: () => apiClient.get('/health/database'),
    matlab: () => apiClient.get('/health/matlab'),
    detailed: () => apiClient.get('/health/detailed'),
  },

  // Models endpoints
  models: {
    list: (params?: any) => apiClient.get('/models/', { params }),
    get: (id: number) => apiClient.get(`/models/${id}`),
    create: (data: any) => apiClient.post('/models/', data),
    update: (id: number, data: any) => apiClient.put(`/models/${id}`, data),
    delete: (id: number) => apiClient.delete(`/models/${id}`),
    validate: (id: number) => apiClient.post(`/models/${id}/validate`),
    getInfo: (id: number) => apiClient.get(`/models/${id}/info`),
    upload: (formData: FormData) => apiClient.post('/models/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  },

  // Test runs endpoints
  testRuns: {
    list: (params?: any) => apiClient.get('/test-runs/', { params }),
    get: (id: number) => apiClient.get(`/test-runs/${id}`),
    create: (data: any) => apiClient.post('/test-runs/', data),
    execute: (id: number) => apiClient.post(`/test-runs/${id}/execute`),
    cancel: (id: number) => apiClient.post(`/test-runs/${id}/cancel`),
    getResults: (id: number) => apiClient.get(`/test-runs/${id}/results`),
    generateReport: (id: number) => apiClient.post(`/test-runs/${id}/report`),
    getStatus: (id: number) => apiClient.get(`/test-runs/${id}/status`),
    downloadResults: (id: number) => apiClient.get(`/test-runs/${id}/download`, { responseType: 'blob' }),
    downloadLogs: (id: number) => apiClient.get(`/test-runs/${id}/logs/download`, { responseType: 'blob' }),
  },

  // Users endpoints
  users: {
    list: (params?: any) => apiClient.get('/users', { params }),
    get: (id: number) => apiClient.get(`/users/${id}`),
  },

  // Reports endpoints
  reports: {
    getAnalytics: (params?: any) => apiClient.get('/reports/analytics', { params }),
    getTestTrends: (params?: any) => apiClient.get('/reports/trends', { params }),
    getModelPerformance: (params?: any) => apiClient.get('/reports/model-performance', { params }),
    exportPDF: (params?: any) => apiClient.get('/reports/export/pdf', { params, responseType: 'blob' }),
    exportExcel: (params?: any) => apiClient.get('/reports/export/excel', { params, responseType: 'blob' }),
  },

  // Dashboard data
  getDashboardData: async () => {
    try {
      // Fetch multiple endpoints in parallel
      const [modelsResponse, testRunsResponse] = await Promise.all([
        apiClient.get('/models'),
        apiClient.get('/test-runs'),
      ]);

      const models = modelsResponse.data;
      const testRuns = testRunsResponse.data;

      // Calculate statistics
      const totalModels = models.length;
      const today = new Date().toISOString().split('T')[0];
      const testRunsToday = testRuns.filter((tr: any) => 
        tr.created_at?.startsWith(today)
      ).length;
      const successfulTests = testRuns.filter((tr: any) => 
        tr.status === 'completed'
      ).length;
      const failedTests = testRuns.filter((tr: any) => 
        tr.status === 'failed'
      ).length;

      // Get recent test runs
      const recentTestRuns = testRuns
        .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5);

      return {
        totalModels,
        testRunsToday,
        successfulTests,
        failedTests,
        recentTestRuns,
      };
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      return {
        totalModels: 0,
        testRunsToday: 0,
        successfulTests: 0,
        failedTests: 0,
        recentTestRuns: [],
      };
    }
  },
};

export default apiClient;

// Attempt silent refresh on 401 using refresh token
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const r = await apiClient.post('/auth/refresh', { refresh_token: refresh });
          const newAccess = r.data?.access_token;
          if (newAccess) {
            localStorage.setItem('auth_token', newAccess);
            original.headers.Authorization = `Bearer ${newAccess}`;
            return apiClient(original);
          }
        } catch (_) {
          // fallthrough to logout
        }
      }
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);