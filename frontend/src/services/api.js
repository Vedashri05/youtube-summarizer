import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// Attach the JWT to every request automatically, once the user is logged
// in. Without this, /videos, /chat, and /search all 401 no matter what -
// ChatBox and SemanticSearch don't need any changes themselves, since
// they already go through this shared instance.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// If the token is missing/expired, the backend returns 401. Bounce back
// to a logged-out state instead of leaving the user staring at a broken
// app with silently-failing requests.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

export default api;