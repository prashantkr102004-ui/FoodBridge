import { Bell } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { NOTIFICATIONS_CHANGED_EVENT, notificationService } from "../services/notificationService";

export default function NotificationBell() {
  const { user } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);

  async function loadUnreadCount() {
    if (!user) {
      setUnreadCount(0);
      return;
    }
    try {
      const data = await notificationService.unreadCount();
      setUnreadCount(data.unread_count);
    } catch {
      setUnreadCount(0);
    }
  }

  useEffect(() => {
    loadUnreadCount();
    window.addEventListener(NOTIFICATIONS_CHANGED_EVENT, loadUnreadCount);
    return () => window.removeEventListener(NOTIFICATIONS_CHANGED_EVENT, loadUnreadCount);
  }, [user?.id]);

  if (!user) return null;

  return (
    <Link className="notification-bell" to="/notifications" aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}>
      <Bell size={18} aria-hidden="true" />
      <span>Notifications</span>
      {unreadCount > 0 && <strong>{unreadCount}</strong>}
    </Link>
  );
}
