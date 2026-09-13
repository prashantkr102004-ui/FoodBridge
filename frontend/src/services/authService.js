import apiClient from "../api/client";

export const authService = {
  register(payload) {
    return apiClient.post("/auth/register", payload).then((res) => res.data);
  },
  uploadReceiverImage(file) {
    const formData = new FormData();
    formData.append("image", file);
    return apiClient.post("/uploads/receiver-image", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then((res) => res.data);
  },
  login(payload) {
    return apiClient.post("/auth/login", payload).then((res) => res.data);
  },
  me() {
    return apiClient.get("/auth/me").then((res) => res.data);
  },
  updateLocation(payload) {
    return apiClient.patch("/users/me/location", payload).then((res) => res.data);
  }
};
