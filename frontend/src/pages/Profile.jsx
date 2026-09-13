import { useAuth } from "../context/AuthContext";
import { useState } from "react";
import { getApiErrorMessage } from "../api/client";
import LocationPicker from "../components/LocationPicker";
import { authService } from "../services/authService";
import { formatDate, isValidCoordinatePair } from "../utils/format";

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    location: user.location || "",
    latitude: user.latitude ?? "",
    longitude: user.longitude ?? ""
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function saveLocation(event) {
    event.preventDefault();
    setMessage("");
    setError("");
    if (!form.location.trim()) {
      setError("Location text is required.");
      return;
    }
    if (!isValidCoordinatePair(form.latitude, form.longitude)) {
      setError("Enter a valid latitude and longitude pair.");
      return;
    }

    setSaving(true);
    try {
      const updated = await authService.updateLocation({
        location: form.location,
        latitude: form.latitude === "" ? null : Number(form.latitude),
        longitude: form.longitude === "" ? null : Number(form.longitude)
      });
      updateUser(updated);
      setMessage("Location saved.");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Account</p>
          <h1>My profile</h1>
        </div>
      </div>
      <div className="details-grid">
        <div><span>Name</span><strong>{user.name}</strong></div>
        <div><span>Email</span><strong>{user.email}</strong></div>
        <div><span>Phone</span><strong>{user.phone}</strong></div>
        <div><span>Role</span><strong>{user.role}</strong></div>
        <div><span>Organization</span><strong>{user.organization_name || "Not provided"}</strong></div>
        <div><span>Location</span><strong>{user.location || "Not provided"}</strong></div>
        <div><span>Map location</span><strong>{user.latitude !== null && user.latitude !== undefined && user.longitude !== null && user.longitude !== undefined ? "Saved" : "Not set"}</strong></div>
        <div><span>Status</span><strong>{user.is_active ? "Active" : "Inactive"}</strong></div>
        <div><span>Joined</span><strong>{formatDate(user.created_at)}</strong></div>
      </div>
      <form className="form-panel two-column location-form" onSubmit={saveLocation} noValidate>
        <h2 className="span-2">Location for nearby matching</h2>
        {error && <p className="alert error span-2">{error}</p>}
        {message && <p className="alert success span-2">{message}</p>}
        <label className="span-2">Address or area
          <input name="location" value={form.location} onChange={updateField} required />
        </label>
        <div className="span-2">
          <LocationPicker onLocation={(coords) => setForm((current) => ({ ...current, ...coords }))} />
        </div>
        <button className="button span-2" disabled={saving}>{saving ? "Saving..." : "Save location"}</button>
      </form>
    </section>
  );
}
