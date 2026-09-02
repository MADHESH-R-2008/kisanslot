import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/admin/login', { username, password }),
  me: () => api.get('/auth/me'),
};

// ── Queue ─────────────────────────────────────────────────────────────────────
export const queueAPI = {
  getCentreStatus: (centreId) => api.get(`/queue/centre/${centreId}/status`),
  getAdminList: () => api.get('/queue/admin/list'),
  callNext: () => api.post('/queue/admin/queue/next'),
  pauseQueue: () => api.post('/queue/admin/queue/pause'),
  resumeQueue: () => api.post('/queue/admin/queue/resume'),
  startProcessing: (bookingId) =>
    api.post(`/queue/admin/booking/${bookingId}/start`),
  completeProcessing: (bookingId) =>
    api.post(`/queue/admin/booking/${bookingId}/complete`),
  markNoShow: (bookingId) =>
    api.post(`/queue/admin/booking/${bookingId}/no_show`),
  updateStatus: (bookingId, status) =>
    api.put(`/queue/admin/booking/${bookingId}/status`, { status }),
};

// ── Centres ───────────────────────────────────────────────────────────────────
export const centreAPI = {
  list: () => api.get('/centres/'),
  create: (data) => api.post('/centres/', data),
  update: (id, data) => api.put(`/centres/${id}`, data),
  remove: (id) => api.delete(`/centres/${id}`),
};

// ── Counters ──────────────────────────────────────────────────────────────────
export const counterAPI = {
  list: () => api.get('/counters/'),
  create: (data) => api.post('/counters/', data),
  update: (id, data) => api.put(`/counters/${id}`, data),
  remove: (id) => api.delete(`/counters/${id}`),
};

// ── Bookings ──────────────────────────────────────────────────────────────────
export const bookingAPI = {
  list: () => api.get('/bookings/admin/all'),
};

// ── Procurement ───────────────────────────────────────────────────────────────
export const procurementAPI = {
  list: (centreId) => api.get(`/procurement/centre/${centreId}`),
  start: (bookingId) => api.post(`/procurement/${bookingId}/start`),
  complete: (bookingId, data) => api.put(`/procurement/${bookingId}/complete`, data),
};

// ── Notifications ─────────────────────────────────────────────────────────────
export const notificationAPI = {
  list: () => api.get('/notifications/'),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
};

export default api;
