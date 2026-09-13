import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DonationCard from "../components/DonationCard";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import QuantityTotals from "../components/QuantityTotals";
import StatCard from "../components/StatCard";
import { dashboardService } from "../services/dashboardService";

export default function DonorDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardService.donor().then(setData).catch(() => setError("Could not load donor dashboard."));
  }, []);

  if (error) return <PageState title="Dashboard unavailable" message={error} />;
  if (!data) return <LoadingSpinner label="Loading donor dashboard" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Donor dashboard</p>
          <h1>Your donation summary</h1>
        </div>
        <Link className="button" to="/donor/post">Post food</Link>
      </div>
      <div className="stats-grid">
        <StatCard label="Total" value={data.total_donations} />
        <StatCard label="Available" value={data.available_donations} />
        <StatCard label="Accepted" value={data.accepted_donations} />
        <StatCard label="Collected" value={data.collected_donations} />
        <StatCard label="Distributed" value={data.distributed_donations} />
        <StatCard label="Cancelled" value={data.cancelled_donations} />
        <StatCard label="Expired" value={data.expired_donations} />
      </div>
      <section className="panel">
        <h2>Quantity donated by unit</h2>
        <QuantityTotals totals={data.total_quantity_donated} />
      </section>
      <section>
        <div className="section-heading">
          <h2>Recent donations</h2>
          <Link to="/donor/donations">View all</Link>
        </div>
        <div className="list-stack">
          {data.recent_donations?.length ? data.recent_donations.map((donation) => (
            <DonationCard key={donation.id} donation={donation} detailPath={`/donor/donations/${donation.id}`} />
          )) : <PageState title="No donations yet" message="Create your first donation when surplus food is available." />}
        </div>
      </section>
    </section>
  );
}
