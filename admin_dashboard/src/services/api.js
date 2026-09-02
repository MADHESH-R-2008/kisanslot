import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (username, password) => api.post('/auth/admin/login', { username, password }),
};

export const queueAPI = {
  getCentreStatus: (centreId) => api.get(`/queue/centre/${centreId}/status`),
  callNext: () => api.post('/queue/admin/queue/next'),
  startProcessing: (bookingId) => api.post(`/queue/admin/booking/${bookingId}/start`),
  completeProcessing: (bookingId) => api.post(`/queue/admin/booking/${bookingId}/complete`),
  markNoShow: (bookingId) => api.post(`/queue/admin/booking/${bookingId}/no_show`),
};

export default api;
