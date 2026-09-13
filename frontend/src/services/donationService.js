import apiClient from "../api/client";
import { notifyNotificationsChanged } from "./notificationService";

export const donationService = {
  create(payload) {
    return apiClient.post("/donations", payload).then((res) => res.data);
  },
  uploadImage(file) {
    const formData = new FormData();
    formData.append("image", file);
    return apiClient.post("/uploads/donation-image", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then((res) => res.data);
  },
  my(status) {
    const params = status ? { status } : {};
    return apiClient.get("/donations/my", { params }).then((res) => res.data);
  },
  available(filters = {}) {
    return apiClient.get("/donations", { params: filters }).then((res) => res.data);
  },
  nearby(filters = {}) {
    return apiClient.get("/donations/nearby", { params: filters }).then((res) => res.data);
  },
  detail(id) {
    return apiClient.get(`/donations/${id}`).then((res) => res.data);
  },
  update(id, payload) {
    return apiClient.patch(`/donations/${id}`, payload).then((res) => res.data);
  },
  cancel(id) {
    return apiClient.post(`/donations/${id}/cancel`).then((res) => res.data);
  },
  accept(id) {
    return apiClient.post(`/donations/${id}/accept`).then((res) => {
      notifyNotificationsChanged();
      return res.data;
    });
  },
  collect(id) {
    return apiClient.post(`/donations/${id}/collect`).then((res) => {
      notifyNotificationsChanged();
      return res.data;
    });
  },
  distribute(id) {
    return apiClient.post(`/donations/${id}/distribute`).then((res) => {
      notifyNotificationsChanged();
      return res.data;
    });
  },
  accepted(status) {
    const params = status ? { status } : {};
    return apiClient.get("/donations/accepted/my", { params }).then((res) => res.data);
  }
};
