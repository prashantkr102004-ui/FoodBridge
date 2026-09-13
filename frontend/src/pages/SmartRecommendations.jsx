import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import StatusBadge from "../components/StatusBadge";
import { donationService } from "../services/donationService";
import { recommendationService } from "../services/recommendationService";
import { formatDate, formatDistance, formatQuantity, formatTimeRemaining } from "../utils/format";

const breakdownLabels = {
  distance: "Distance",
  urgency: "Urgency",
  quantity: "Quantity",
  preference: "Preference"
};

export default function SmartRecommendations() {
  const [filters, setFilters] = useState({ radius_km: "20", food_type: "", quantity_unit: "", limit: "10" });
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    try {
      setRecommendations(await recommendationService.donations(params));
    } catch (err) {
      setError(getApiErrorMessage(err));
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filters.radius_km, filters.food_type, filters.quantity_unit, filters.limit]);

  function updateFilter(event) {
    setFilters((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function acceptDonation(id) {
    if (!window.confirm("Accept this recommended donation?")) return;
    setActionId(id);
    setError("");
    try {
      await donationService.accept(id);
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setActionId("");
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Receiver</p>
          <h1>Smart recommendations</h1>
        </div>
      </div>

      <div className="toolbar">
        <label>Radius
          <select name="radius_km" value={filters.radius_km} onChange={updateFilter}>
            <option value="5">5 km</option>
            <option value="10">10 km</option>
            <option value="20">20 km</option>
            <option value="50">50 km</option>
          </select>
        </label>
        <label>Food type
          <select name="food_type" value={filters.food_type} onChange={updateFilter}>
            <option value="">All</option>
            <option value="VEGETARIAN">VEGETARIAN</option>
            <option value="NON_VEGETARIAN">NON VEGETARIAN</option>
            <option value="VEGAN">VEGAN</option>
            <option value="OTHER">OTHER</option>
          </select>
        </label>
        <label>Unit
          <select name="quantity_unit" value={filters.quantity_unit} onChange={updateFilter}>
            <option value="">All</option>
            <option value="MEALS">MEALS</option>
            <option value="PACKETS">PACKETS</option>
            <option value="KG">KG</option>
            <option value="OTHER">OTHER</option>
          </select>
        </label>
      </div>

      {error && <p className="alert error">{error}</p>}
      {loading ? <LoadingSpinner label="Loading smart recommendations" /> : (
        <div className="recommendation-list">
          {recommendations.length ? recommendations.map((donation, index) => (
            <article className="recommendation-card" key={donation.id}>
              <div className="match-rank">
                <span>#{index + 1}</span>
                <strong>{donation.match_score}/100</strong>
                <small>Match Score</small>
              </div>
              <div className="recommendation-body">
                <div className="row-between">
                  <div>
                    <h3>{donation.food_name}</h3>
                    <p className="muted">
                      {donation.food_type.replace("_", " ")} - {formatQuantity(donation.quantity, donation.quantity_unit)}
                    </p>
                  </div>
                  <StatusBadge status={donation.status} />
                </div>
                <div className="recommendation-meta">
                  <span>{formatDistance(donation.distance_km)}</span>
                  <span>{formatTimeRemaining(donation.available_until)}</span>
                  <span>{formatDate(donation.available_until)}</span>
                </div>
                <div className="score-breakdown">
                  {Object.entries(donation.score_breakdown).map(([key, value]) => (
                    <div key={key}>
                      <span>{breakdownLabels[key]}</span>
                      <div className="score-bar" aria-label={`${breakdownLabels[key]} score ${value}`}>
                        <span style={{ width: `${value}%` }} />
                      </div>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="section-label">Why recommended</p>
                  <ul className="reason-list">
                    {donation.reasons.map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                </div>
              </div>
              <div className="actions">
                <Link className="button secondary" to={`/receiver/donations/${donation.id}`}>View</Link>
                <button className="button" type="button" disabled={actionId === donation.id} onClick={() => acceptDonation(donation.id)}>
                  {actionId === donation.id ? "Accepting..." : "Accept Donation"}
                </button>
              </div>
            </article>
          )) : <PageState title="No recommendations found" message="Try a larger radius, clear filters, or check Available Food." />}
        </div>
      )}
    </section>
  );
}
