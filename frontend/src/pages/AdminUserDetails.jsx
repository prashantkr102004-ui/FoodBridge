import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import { useAuth } from "../context/AuthContext";
import { adminService } from "../services/adminService";
import { formatDate } from "../utils/format";

export default function AdminUserDetails() {
  const { id } = useParams();
  const { user: currentUser } = useAuth();
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setUser(await adminService.user(id));
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function toggleActive() {
    try {
      user.is_active ? await adminService.deactivateUser(id) : await adminService.activateUser(id);
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }

  if (error && !user) return <PageState title="User unavailable" message={error} />;
  if (!user) return <LoadingSpinner label="Loading user" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Admin user</p>
          <h1>{user.name}</h1>
        </div>
        {user.id !== currentUser.id && (
          <button className={user.is_active ? "button danger" : "button"} onClick={toggleActive}>
            {user.is_active ? "Deactivate" : "Activate"}
          </button>
        )}
      </div>
      {error && <p className="alert error">{error}</p>}
      <div className="details-grid">
        <div><span>Email</span><strong>{user.email}</strong></div>
        <div><span>Phone</span><strong>{user.phone}</strong></div>
        <div><span>Role</span><strong>{user.role}</strong></div>
        <div><span>Status</span><strong>{user.is_active ? "Active" : "Inactive"}</strong></div>
        <div><span>Organization</span><strong>{user.organization_name || "Not provided"}</strong></div>
        <div><span>Location</span><strong>{user.location || "Not provided"}</strong></div>
        <div><span>Created</span><strong>{formatDate(user.created_at)}</strong></div>
        <div><span>Created donations</span><strong>{user.donations_created}</strong></div>
        <div><span>Accepted donations</span><strong>{user.donations_accepted}</strong></div>
        <div><span>Distributed donations</span><strong>{user.donations_distributed}</strong></div>
      </div>
    </section>
  );
}
