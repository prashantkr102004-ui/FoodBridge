import apiClient from "../api/client";

export const NOTIFICATIONS_CHANGED_EVENT = "foodbridge:notifications-changed";

export function notifyNotificationsChanged() {
  window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED_EVENT));
}

export const notificationService = {
  list(params = {}) {
    return apiClient.get("/notifications", { params }).then((res) => res.data);
  },
  unreadCount() {
    return apiClient.get("/notifications/unread-count").then((res) => res.data);
  },
  markRead(id) {
    return apiClient.post(`/notifications/${id}/read`).then((res) => {
      notifyNotificationsChanged();
      return res.data;
    });
  },
  markAllRead() {
    return apiClient.post("/notifications/read-all").then((res) => {
      notifyNotificationsChanged();
      return res.data;
    });
  }
};
