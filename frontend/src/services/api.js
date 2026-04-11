import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 35000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("eds_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("eds_token");
      window.location.reload();
    }
    return Promise.reject(err);
  }
);
