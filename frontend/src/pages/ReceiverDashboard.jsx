import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DonationCard from "../components/DonationCard";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import QuantityTotals from "../components/QuantityTotals";
import StatCard from "../components/StatCard";
import { dashboardService } from "../services/dashboardService";

export default function ReceiverDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardService.receiver().then(setData).catch(() => setError("Could not load receiver dashboard."));
  }, []);

  if (error) return <PageState title="Dashboard unavailable" message={error} />;
  if (!data) return <LoadingSpinner label="Loading receiver dashboard" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Receiver dashboard</p>
          <h1>Your accepted food work</h1>
        </div>
        <Link className="button" to="/receiver/available">Find food</Link>
      </div>
      <div className="stats-grid">
        <StatCard label="Available now" value={data.available_donations_count} />
        <StatCard label="Accepted" value={data.accepted_count} />
        <StatCard label="Collected" value={data.collected_count} />
        <StatCard label="Distributed" value={data.distributed_count} />
      </div>
      <section className="panel">
        <h2>Rescued quantity by unit</h2>
        <QuantityTotals totals={data.total_rescued_quantity} />
      </section>
      <section>
        <div className="section-heading">
          <h2>Recent accepted donations</h2>
          <Link to="/receiver/accepted">View all</Link>
        </div>
        <div className="list-stack">
          {data.recent_accepted_donations?.length ? data.recent_accepted_donations.map((donation) => (
            <DonationCard key={donation.id} donation={donation} detailPath={`/receiver/donations/${donation.id}`} />
          )) : <PageState title="No accepted donations yet" message="Browse available food and accept a suitable donation." />}
        </div>
      </section>
    </section>
  );
}
