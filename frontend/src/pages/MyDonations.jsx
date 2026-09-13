import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import DonationCard from "../components/DonationCard";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import { donationService } from "../services/donationService";

export default function MyDonations() {
  const [donations, setDonations] = useState([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setDonations(await donationService.my(status));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [status]);

  async function cancelDonation(id) {
    if (!window.confirm("Cancel this available donation?")) return;
    try {
      await donationService.cancel(id);
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Donor</p>
          <h1>My donations</h1>
        </div>
        <Link className="button" to="/donor/post">Post food</Link>
      </div>
      <div className="toolbar">
        <label>Status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="AVAILABLE">AVAILABLE</option>
            <option value="ACCEPTED">ACCEPTED</option>
            <option value="COLLECTED">COLLECTED</option>
            <option value="DISTRIBUTED">DISTRIBUTED</option>
            <option value="CANCELLED">CANCELLED</option>
            <option value="EXPIRED">EXPIRED</option>
          </select>
        </label>
      </div>
      {error && <p className="alert error">{error}</p>}
      {loading ? <LoadingSpinner label="Loading donations" /> : (
        <div className="list-stack">
          {donations.length ? donations.map((donation) => (
            <DonationCard key={donation.id} donation={donation} detailPath={`/donor/donations/${donation.id}`}>
              {donation.status === "AVAILABLE" && (
                <>
                  <Link className="button secondary" to={`/donor/donations/${donation.id}/edit`}>Edit</Link>
                  <button className="button danger" onClick={() => cancelDonation(donation.id)}>Cancel</button>
                </>
              )}
            </DonationCard>
          )) : <PageState title="No donations found" message="Try another status filter or post a new donation." />}
        </div>
      )}
    </section>
  );
}
