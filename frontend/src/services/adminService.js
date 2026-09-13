import apiClient from "../api/client";

export const adminService = {
  dashboard() {
    return apiClient.get("/admin/dashboard").then((res) => res.data);
  },
  users(params) {
    return apiClient.get("/admin/users", { params }).then((res) => res.data);
  },
  user(id) {
    return apiClient.get(`/admin/users/${id}`).then((res) => res.data);
  },
  deactivateUser(id) {
    return apiClient.post(`/admin/users/${id}/deactivate`).then((res) => res.data);
  },
  activateUser(id) {
    return apiClient.post(`/admin/users/${id}/activate`).then((res) => res.data);
  },
  donations(params) {
    return apiClient.get("/admin/donations", { params }).then((res) => res.data);
  },
  donation(id) {
    return apiClient.get(`/admin/donations/${id}`).then((res) => res.data);
  }
};
