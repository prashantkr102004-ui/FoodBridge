import apiClient from "../api/client";

export const recommendationService = {
  donations(filters = {}) {
    return apiClient.get("/recommendations/donations", { params: filters }).then((res) => res.data);
  }
};
