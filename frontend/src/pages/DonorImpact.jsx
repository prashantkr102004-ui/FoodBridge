import { useEffect, useState } from "react";
import LoadingSpinner from "../components/LoadingSpinner";
import MonthlyActivity from "../components/MonthlyActivity";
import PageState from "../components/PageState";
import QuantityTotals from "../components/QuantityTotals";
import RecentImpact from "../components/RecentImpact";
import SimpleBarChart from "../components/SimpleBarChart";
import StatCard from "../components/StatCard";
import { analyticsService } from "../services/analyticsService";

export default function DonorImpact() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    analyticsService.donor().then(setData).catch(() => setError("Could not load donor impact analytics."));
  }, []);

  if (error) return <PageState title="Impact unavailable" message={error} />;
  if (!data) return <LoadingSpinner text="Loading impact analytics..." />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Donor impact</p>
          <h1>Your food impact</h1>
        </div>
      </div>
      <div className="stats-grid">
        <StatCard label="Total Donations" value={data.total_donations} />
        <StatCard label="Successfully Distributed" value={data.distributed_donations} />
        <StatCard label="Active Donations" value={data.active_donations} />
        <StatCard label="Success Rate" value={`${data.success_rate}%`} />
      </div>
      <section className="panel">
        <h2>Food donated by unit</h2>
        <QuantityTotals totals={data.quantity_by_unit} />
      </section>
      <section className="panel">
        <h2>Successfully distributed by unit</h2>
        <QuantityTotals totals={data.distributed_quantity_by_unit} />
      </section>
      <SimpleBarChart title="Food type breakdown" data={data.food_type_breakdown} />
      <MonthlyActivity items={data.monthly_activity} />
      <RecentImpact items={data.recent_impact} />
    </section>
  );
}
