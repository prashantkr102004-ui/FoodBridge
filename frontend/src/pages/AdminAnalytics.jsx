import { useEffect, useState } from "react";
import { getApiErrorMessage } from "../api/client";
import LoadingSpinner from "../components/LoadingSpinner";
import MonthlyActivity from "../components/MonthlyActivity";
import PageState from "../components/PageState";
import QuantityTotals from "../components/QuantityTotals";
import SimpleBarChart from "../components/SimpleBarChart";
import StatCard from "../components/StatCard";
import { analyticsService } from "../services/analyticsService";

function todayStamp() {
  return new Date().toISOString().slice(0, 10);
}

export default function AdminAnalytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [exportStatus, setExportStatus] = useState("");

  useEffect(() => {
    analyticsService.admin().then(setData).catch(() => setError("Could not load admin analytics."));
  }, []);

  async function exportCsv() {
    setExportStatus("Preparing export...");
    try {
      const blob = await analyticsService.exportCsv();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `foodbridge-impact-report-${todayStamp()}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setExportStatus("CSV export ready.");
    } catch (err) {
      setExportStatus(getApiErrorMessage(err));
    }
  }

  if (error) return <PageState title="Analytics unavailable" message={error} />;
  if (!data) return <LoadingSpinner text="Loading admin analytics..." />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Admin analytics</p>
          <h1>Platform impact</h1>
        </div>
        <button className="button" type="button" onClick={exportCsv}>Export CSV</button>
      </div>
      {exportStatus && <p className="alert success">{exportStatus}</p>}
      <div className="stats-grid">
        <StatCard label="Total Users" value={data.total_users} />
        <StatCard label="Total Donations" value={data.total_donations} />
        <StatCard label="Successfully Distributed" value={data.total_distributed} />
        <StatCard label="Success Rate" value={`${data.distribution_success_rate}%`} />
        <StatCard label="Cancelled" value={data.total_cancelled} />
        <StatCard label="Expired" value={data.total_expired} />
      </div>
      <section className="panel">
        <h2>Distributed quantity by unit</h2>
        <QuantityTotals totals={data.quantity_distributed_by_unit} />
      </section>
      <div className="analytics-grid">
        <SimpleBarChart title="Users by role" data={data.users_by_role} />
        <SimpleBarChart title="Donation status breakdown" data={data.donations_by_status} />
        <SimpleBarChart title="Food type breakdown" data={data.food_type_breakdown} />
      </div>
      <MonthlyActivity items={data.monthly_donation_activity} />
    </section>
  );
}
