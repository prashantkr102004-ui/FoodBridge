import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail;
    if (error.response?.status === 401 || detail === "This account is deactivated") {
      window.dispatchEvent(new Event("foodbridge:unauthorized"));
    }
    return Promise.reject(error);
  }
);

export function setAuthToken(token) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}

export function getApiErrorMessage(error) {
  if (!error.response) {
    return "Unable to reach FoodBridge API. Please check that the backend is running.";
  }
  const detail = error.response.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(", ");
  }
  return detail || "Something went wrong. Please try again.";
}

export default apiClient;
