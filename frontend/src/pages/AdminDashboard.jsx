import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import QuantityTotals from "../components/QuantityTotals";
import StatCard from "../components/StatCard";
import { adminService } from "../services/adminService";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    adminService.dashboard().then(setData).catch(() => setError("Could not load admin dashboard."));
  }, []);

  if (error) return <PageState title="Admin dashboard unavailable" message={error} />;
  if (!data) return <LoadingSpinner label="Loading admin dashboard" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Platform summary</h1>
        </div>
        <div className="actions">
          <Link className="button secondary" to="/admin/users">Users</Link>
          <Link className="button secondary" to="/admin/donations">Donations</Link>
        </div>
      </div>
      <div className="stats-grid">
        <StatCard label="Users" value={data.total_users} />
        <StatCard label="Donors" value={data.total_donors} />
        <StatCard label="NGOs" value={data.total_ngos} />
        <StatCard label="Volunteers" value={data.total_volunteers} />
        <StatCard label="Admins" value={data.total_admins} />
        <StatCard label="Donations" value={data.total_donations} />
        <StatCard label="Available" value={data.available_donations} />
        <StatCard label="Accepted" value={data.accepted_donations} />
        <StatCard label="Collected" value={data.collected_donations} />
        <StatCard label="Distributed" value={data.distributed_donations} />
        <StatCard label="Cancelled" value={data.cancelled_donations} />
        <StatCard label="Expired" value={data.expired_donations} />
      </div>
      <section className="panel">
        <h2>Rescued quantity by unit</h2>
        <QuantityTotals totals={data.quantity_rescued_by_unit} />
      </section>
    </section>
  );
}
