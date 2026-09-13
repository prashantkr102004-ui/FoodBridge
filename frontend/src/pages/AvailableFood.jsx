import { useEffect, useState } from "react";
import { getApiErrorMessage } from "../api/client";
import DonationCard from "../components/DonationCard";
import LoadingSpinner from "../components/LoadingSpinner";
import { NearbyDonationsMap } from "../components/MapView";
import PageState from "../components/PageState";
import { useAuth } from "../context/AuthContext";
import { donationService } from "../services/donationService";
import { formatDistance } from "../utils/format";

export default function AvailableFood() {
  const [filters, setFilters] = useState({ food_type: "", quantity_unit: "" });
  const [browseMode, setBrowseMode] = useState("available");
  const [radiusKm, setRadiusKm] = useState("10");
  const [donations, setDonations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { user } = useAuth();

  async function load() {
    setLoading(true);
    setError("");
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    if (browseMode === "nearby") {
      params.radius_km = radiusKm;
    }
    try {
      setDonations(
        browseMode === "nearby"
          ? await donationService.nearby(params)
          : await donationService.available(params)
      );
    } catch (err) {
      setError(getApiErrorMessage(err));
      setDonations([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filters.food_type, filters.quantity_unit, browseMode, radiusKm]);

  function updateFilter(event) {
    setFilters((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function acceptDonation(id) {
    if (!window.confirm("Accept this donation?")) return;
    try {
      await donationService.accept(id);
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Receiver</p>
          <h1>Available food</h1>
        </div>
      </div>
      <div className="toolbar">
        <div className="segmented">
          <button className={browseMode === "available" ? "active" : ""} onClick={() => setBrowseMode("available")} type="button">
            Available Food
          </button>
          <button className={browseMode === "nearby" ? "active" : ""} onClick={() => setBrowseMode("nearby")} type="button">
            Nearby Food
          </button>
        </div>
        <label>Food type
          <select name="food_type" value={filters.food_type} onChange={updateFilter}>
            <option value="">All</option>
            <option value="VEGETARIAN">VEGETARIAN</option>
            <option value="NON_VEGETARIAN">NON_VEGETARIAN</option>
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
        {browseMode === "nearby" && (
          <label>Radius
            <select value={radiusKm} onChange={(event) => setRadiusKm(event.target.value)}>
              <option value="5">5 km</option>
              <option value="10">10 km</option>
              <option value="20">20 km</option>
              <option value="50">50 km</option>
            </select>
          </label>
        )}
      </div>
      {error && <p className="alert error">{error}</p>}
      {loading ? <LoadingSpinner label="Loading available donations" /> : (
        <>
          {browseMode === "nearby" && <NearbyDonationsMap user={user} donations={donations} />}
          <div className="list-stack">
            {donations.length ? donations.map((donation) => (
              <DonationCard key={donation.id} donation={donation} detailPath={`/receiver/donations/${donation.id}`}>
                {donation.distance_km !== undefined && <span className="distance-pill">{formatDistance(donation.distance_km)}</span>}
                <button className="button" onClick={() => acceptDonation(donation.id)}>Accept</button>
              </DonationCard>
            )) : <PageState title={browseMode === "nearby" ? "No nearby food found" : "No food available"} message="Try another radius, clear filters, or use the normal available list." />}
          </div>
        </>
      )}
    </section>
  );
}
