import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('api_token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('api_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// API methods
export const jobsApi = {
  list: (params?: any) => apiClient.get('/jobs', { params }),
  get: (id: number) => apiClient.get(`/jobs/${id}`),
  create: (data: any) => apiClient.post('/jobs', data),
  update: (id: number, data: any) => apiClient.patch(`/jobs/${id}`, data),
  delete: (id: number) => apiClient.delete(`/jobs/${id}`),
  process: (data: any) => apiClient.post('/jobs/process', data),
  analyze: (id: number) => apiClient.post(`/analysis/jobs/${id}/analyze`),
  generateDocuments: (id: number) => apiClient.post(`/documents/jobs/${id}/generate`),
  getDocuments: (id: number) => apiClient.get(`/documents/jobs/${id}`),
  listDriveFiles: (folderId?: string) => apiClient.get('/jobs/drive/list', { params: { folder_id: folderId } }),
  importFromDrive: (fileId: string) => apiClient.post(`/jobs/import-from-drive/${fileId}`),
};

export const applicationsApi = {
  list: (statusFilter?: string) => apiClient.get('/ats/applications', { params: { status: statusFilter } }),
  updateStatus: (id: number, data: any) => apiClient.post(`/ats/jobs/${id}/status`, data),
  getTimeline: (id: number) => apiClient.get(`/ats/jobs/${id}/timeline`),
  getStatistics: () => apiClient.get('/ats/statistics'),
  addNote: (data: any) => apiClient.post('/ats/notes', data),
};

export const recommendationsApi = {
  list: (params?: any) => apiClient.get('/recommendations', { params }),
  learnClick: (id: number) => apiClient.post(`/recommendations/learn/click/${id}`),
  learnDismiss: (id: number, reason: string) =>
    apiClient.post(`/recommendations/learn/dismiss/${id}`, { reason }),
};

export const interviewsApi = {
  upcoming: (params?: any) => apiClient.get('/ats/interviews/upcoming', { params }),
  create: (data: any) => apiClient.post('/ats/interviews', data),
  update: (id: number, data: any) => apiClient.put(`/ats/interviews/${id}`, data),
  getForJob: (jobId: number) => apiClient.get(`/ats/jobs/${jobId}/interviews`),
};

export const followUpsApi = {
  due: (params?: any) => apiClient.get('/followup/due', { params }),
  forJob: (jobId: number) => apiClient.get(`/followup/jobs/${jobId}`),
  markSent: (id: number, data: any) => apiClient.post(`/followup/${id}/sent`, data),
};

export const analyticsApi = {
  overview: () => apiClient.get('/analytics/overview'),
  funnel: (params?: any) => apiClient.get('/analytics/funnel', { params }),
  trends: (params?: any) => apiClient.get('/analytics/trends', { params }),
  successPatterns: () => apiClient.get('/analytics/success-patterns'),
};

export const cacheApi = {
  stats: () => apiClient.get('/cache/stats'),
  clear: (namespace: string) => apiClient.delete(`/cache/${namespace}`),
};

export const scrapingApi = {
  trigger: (data: any) => apiClient.post('/scraping/trigger', data),
  status: (taskId: string) => apiClient.get(`/scraping/status/${taskId}`),
};

export const skillsApi = {
  analyze: () => apiClient.get('/skills/analyze'),
  getGaps: () => apiClient.get('/skills/gaps'),
};

export const researchApi = {
  company: (companyName: string) => apiClient.get(`/research/company/${companyName}`),
  forJob: (jobId: number) => apiClient.get(`/research/jobs/${jobId}`),
};

export default apiClient;
