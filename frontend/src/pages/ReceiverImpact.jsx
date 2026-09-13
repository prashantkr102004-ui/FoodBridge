import { useEffect, useState } from "react";
import LoadingSpinner from "../components/LoadingSpinner";
import MonthlyActivity from "../components/MonthlyActivity";
import PageState from "../components/PageState";
import QuantityTotals from "../components/QuantityTotals";
import RecentImpact from "../components/RecentImpact";
import SimpleBarChart from "../components/SimpleBarChart";
import StatCard from "../components/StatCard";
import { analyticsService } from "../services/analyticsService";

export default function ReceiverImpact() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    analyticsService.receiver().then(setData).catch(() => setError("Could not load receiver impact analytics."));
  }, []);

  if (error) return <PageState title="Impact unavailable" message={error} />;
  if (!data) return <LoadingSpinner text="Loading receiver impact..." />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Receiver impact</p>
          <h1>Food rescued by you</h1>
        </div>
      </div>
      <div className="stats-grid">
        <StatCard label="Accepted Donations" value={data.total_accepted} />
        <StatCard label="Currently Accepted" value={data.currently_accepted} />
        <StatCard label="Collected" value={data.collected} />
        <StatCard label="Distributed" value={data.distributed} />
        <StatCard label="Completion Rate" value={`${data.completion_rate}%`} />
      </div>
      <section className="panel">
        <h2>Food rescued by unit</h2>
        <QuantityTotals totals={data.quantity_rescued_by_unit} />
      </section>
      <SimpleBarChart title="Food type breakdown" data={data.food_type_breakdown} />
      <MonthlyActivity items={data.monthly_activity} />
      <RecentImpact items={data.recent_impact} />
    </section>
  );
}
