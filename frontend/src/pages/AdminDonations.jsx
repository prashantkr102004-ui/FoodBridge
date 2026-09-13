import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import Pagination from "../components/Pagination";
import StatusBadge from "../components/StatusBadge";
import { adminService } from "../services/adminService";
import { formatDate, formatQuantity } from "../utils/format";

export default function AdminDonations() {
  const [params, setParams] = useState({ page: 1, page_size: 10, status: "", food_type: "", donor_id: "", accepted_by_user_id: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      const query = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== ""));
      try {
        setData(await adminService.donations(query));
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params]);

  function setParam(key, value) {
    setParams((current) => ({ ...current, [key]: value, page: key === "page" ? value : 1 }));
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Donations</h1>
        </div>
      </div>
      <div className="toolbar">
        <label>Status
          <select value={params.status} onChange={(event) => setParam("status", event.target.value)}>
            <option value="">All</option>
            <option value="AVAILABLE">AVAILABLE</option>
            <option value="ACCEPTED">ACCEPTED</option>
            <option value="COLLECTED">COLLECTED</option>
            <option value="DISTRIBUTED">DISTRIBUTED</option>
            <option value="CANCELLED">CANCELLED</option>
            <option value="EXPIRED">EXPIRED</option>
          </select>
        </label>
        <label>Food type
          <select value={params.food_type} onChange={(event) => setParam("food_type", event.target.value)}>
            <option value="">All</option>
            <option value="VEGETARIAN">VEGETARIAN</option>
            <option value="NON_VEGETARIAN">NON_VEGETARIAN</option>
            <option value="VEGAN">VEGAN</option>
            <option value="OTHER">OTHER</option>
          </select>
        </label>
        <label>Donor ID
          <input value={params.donor_id} onChange={(event) => setParam("donor_id", event.target.value)} />
        </label>
        <label>Accepted by ID
          <input value={params.accepted_by_user_id} onChange={(event) => setParam("accepted_by_user_id", event.target.value)} />
        </label>
      </div>
      {error && <p className="alert error">{error}</p>}
      {loading ? <LoadingSpinner label="Loading donations" /> : data?.items?.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Food</th><th>Quantity</th><th>Status</th><th>Donor</th><th>Accepted by</th><th>Created</th><th></th></tr></thead>
              <tbody>
                {data.items.map((donation) => (
                  <tr key={donation.id}>
                    <td>{donation.food_name}</td>
                    <td>{formatQuantity(donation.quantity, donation.quantity_unit)}</td>
                    <td><StatusBadge status={donation.status} /></td>
                    <td>{donation.donor_id}</td>
                    <td>{donation.accepted_by_user_id || "Not accepted"}</td>
                    <td>{formatDate(donation.created_at)}</td>
                    <td><Link className="button secondary" to={`/admin/donations/${donation.id}`}>View</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={(page) => setParam("page", page)} />
        </>
      ) : <PageState title="No donations found" message="Try changing the filters." />}
    </section>
  );
}
