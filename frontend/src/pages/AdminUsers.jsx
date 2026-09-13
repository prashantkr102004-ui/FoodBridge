import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import Pagination from "../components/Pagination";
import { useAuth } from "../context/AuthContext";
import { adminService } from "../services/adminService";

export default function AdminUsers() {
  const { user } = useAuth();
  const [params, setParams] = useState({ page: 1, page_size: 10, role: "", search: "" });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    const query = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== ""));
    try {
      setData(await adminService.users(query));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [params]);

  async function setActive(id, active) {
    try {
      active ? await adminService.activateUser(id) : await adminService.deactivateUser(id);
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Users</h1>
        </div>
      </div>
      <div className="toolbar">
        <label>Role
          <select value={params.role} onChange={(event) => setParams({ ...params, role: event.target.value, page: 1 })}>
            <option value="">All</option>
            <option value="DONOR">DONOR</option>
            <option value="NGO">NGO</option>
            <option value="VOLUNTEER">VOLUNTEER</option>
            <option value="ADMIN">ADMIN</option>
          </select>
        </label>
        <label>Search
          <input value={params.search} onChange={(event) => setParams({ ...params, search: event.target.value, page: 1 })} />
        </label>
      </div>
      {error && <p className="alert error">{error}</p>}
      {loading ? <LoadingSpinner label="Loading users" /> : data?.items?.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>{item.email}</td>
                    <td>{item.role}</td>
                    <td>{item.is_active ? "Active" : "Inactive"}</td>
                    <td className="actions compact">
                      <Link className="button secondary" to={`/admin/users/${item.id}`}>View</Link>
                      {item.id !== user.id && (
                        <button className={item.is_active ? "button danger" : "button"} onClick={() => setActive(item.id, !item.is_active)}>
                          {item.is_active ? "Deactivate" : "Activate"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={(page) => setParams({ ...params, page })} />
        </>
      ) : <PageState title="No users found" message="Try a different role or search term." />}
    </section>
  );
}
