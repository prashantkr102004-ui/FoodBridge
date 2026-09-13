import apiClient from "../api/client";

export const dashboardService = {
  donor() {
    return apiClient.get("/dashboard/donor").then((res) => res.data);
  },
  receiver() {
    return apiClient.get("/dashboard/receiver").then((res) => res.data);
  }
};
