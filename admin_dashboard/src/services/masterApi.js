import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Master API ────────────────────────────────────────────────────────────────
export const masterAPI = {
  // Dashboard & Profile
  dashboard: () => api.get('/master/dashboard'),
  profile: () => api.get('/master/profile'),
  district: () => api.get('/master/district'),

  // Centres
  listCentres: (params) => api.get('/master/centres', { params }),
  getCentre: (id) => api.get(`/master/centres/${id}`),
  createCentre: (data) => api.post('/master/centres', data),
  updateCentre: (id, data) => api.put(`/master/centres/${id}`, data),
  setCentreStatus: (id, isActive) => api.put(`/master/centres/${id}/status`, { is_active: isActive }),
  getCentreOperators: (centreId) => api.get(`/master/centres/${centreId}/operators`),

  // Operators
  createOperator: (data) => api.post('/master/operators', data),
  updateOperator: (id, data) => api.put(`/master/operators/${id}`, data),
  setOperatorStatus: (id, isActive) => api.put(`/master/operators/${id}/status`, { is_active: isActive }),
  assignOperatorCentre: (id, centreId) => api.put(`/master/operators/${id}/centre`, { centre_id: centreId }),

  // District-scoped data
  bookings: () => api.get('/master/bookings'),
  queue: () => api.get('/master/queue'),
  procurement: () => api.get('/master/procurement'),
  payments: () => api.get('/master/payments'),
};

// ── Super Admin Master Management ─────────────────────────────────────────────
export const superAdminAPI = {
  listMasters: () => api.get('/super-admin/masters'),
  createMaster: (data) => api.post('/super-admin/masters', data),
  getMaster: (id) => api.get(`/super-admin/masters/${id}`),
  updateMaster: (id, data) => api.put(`/super-admin/masters/${id}`, data),
  setMasterStatus: (id, isActive) => api.put(`/super-admin/masters/${id}/status`, { is_active: isActive }),
};

export default api;
