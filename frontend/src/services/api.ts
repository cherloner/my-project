import axios from 'axios';

// Create an Axios instance with default config
const api = axios.create({
  baseURL: '/api', // Proxy will handle this in development
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Handle unauthorized (e.g., redirect to login)
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  sendCode: (phone: string, scene: 'register' | 'login') => 
    api.post('/auth/send_code', { phone, scene }),
  
  loginByPhone: (phone: string, code: string) => 
    api.post('/auth/login_by_phone', { phone, code }),
    
  getMe: () => api.get('/user/me'),
};

export const videoApi = {
  getRecommendFeed: (page = 1) => api.get('/feed/recommend', { params: { page } }),
  getVideoDetail: (id: string) => api.get(`/video/${id}`),
};

export const uploadApi = {
  initUpload: (data: any) => api.post('/upload/init', data),
  completeUpload: (data: any) => api.post('/upload/complete', data),
};

export const splitApi = {
  createTask: (data: any) => api.post('/split/tasks', data),
  getTaskStatus: (taskId: string) => api.get(`/split/tasks/${taskId}`),
};

export default api;
