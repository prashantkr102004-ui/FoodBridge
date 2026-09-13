import apiClient from "../api/client";

export const analyticsService = {
  donor() {
    return apiClient.get("/analytics/donor").then((res) => res.data);
  },
  receiver() {
    return apiClient.get("/analytics/receiver").then((res) => res.data);
  },
  admin(params = {}) {
    return apiClient.get("/analytics/admin", { params }).then((res) => res.data);
  },
  exportCsv(status = "DISTRIBUTED") {
    return apiClient.get("/analytics/admin/export.csv", {
      params: { status },
      responseType: "blob"
    }).then((res) => res.data);
  }
};
