import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/";

const api = axios.create({
  baseURL,
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error?.message ||
      "Request failed";
    return Promise.reject({ ...error, friendlyMessage: message });
  },
);

export const getErrorMessage = (error, fallback) => {
  if (error?.friendlyMessage) {
    return error.friendlyMessage;
  }

  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }

  return fallback || "Something went wrong";
};

export default api;
