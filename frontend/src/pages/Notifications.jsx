import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import { useAuth } from "../context/AuthContext";
import { notificationService } from "../services/notificationService";
import { formatDate } from "../utils/format";

function donationPath(role, donationId) {
  if (!donationId) return null;
  if (role === "DONOR") return `/donor/donations/${donationId}`;
  if (role === "NGO" || role === "VOLUNTEER") return `/receiver/donations/${donationId}`;
  if (role === "ADMIN") return `/admin/donations/${donationId}`;
  return null;
}

export default function Notifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await notificationService.list({ page: 1, page_size: 20 });
      setNotifications(data.items);
      setMeta({ total: data.total, page: data.page, page_size: data.page_size });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function markRead(notification) {
    if (notification.is_read) return;
    setActionError("");
    try {
      const updated = await notificationService.markRead(notification.id);
      setNotifications((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    }
  }

  async function markAllRead() {
    setActionError("");
    try {
      await notificationService.markAllRead();
      await load();
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    }
  }

  if (loading) return <LoadingSpinner text="Loading notifications..." />;
  if (error) return <PageState title="Notifications unavailable" message={error} />;

  const unreadCount = notifications.filter((notification) => !notification.is_read).length;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Account</p>
          <h1>Notifications</h1>
        </div>
        <button className="button secondary" type="button" disabled={!unreadCount} onClick={markAllRead}>
          Mark all as read
        </button>
      </div>
      {actionError && <p className="alert error">{actionError}</p>}
      {notifications.length ? (
        <div className="notification-list">
          {notifications.map((notification) => {
            const path = donationPath(user.role, notification.donation_id);
            return (
              <article className={`notification-item ${notification.is_read ? "read" : "unread"}`} key={notification.id}>
                <div>
                  {!notification.is_read && <span className="unread-label">Unread</span>}
                  <h3>{notification.title}</h3>
                  <p>{notification.message}</p>
                  <p className="muted">{formatDate(notification.created_at)}</p>
                </div>
                <div className="actions">
                  {path && <Link className="button secondary" to={path} onClick={() => markRead(notification)}>Open donation</Link>}
                  {!notification.is_read && (
                    <button className="button" type="button" onClick={() => markRead(notification)}>
                      Mark read
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <PageState title="No notifications yet." message="Important donation updates will appear here." />
      )}
      {meta.total > meta.page_size && <p className="muted">Showing latest {notifications.length} of {meta.total} notifications.</p>}
    </section>
  );
}
