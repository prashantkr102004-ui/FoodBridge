import { useEffect, useState } from "react";
import { getApiErrorMessage } from "../api/client";
import DonationCard from "../components/DonationCard";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import { donationService } from "../services/donationService";

export default function MyAcceptedDonations() {
  const [status, setStatus] = useState("");
  const [donations, setDonations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setDonations(await donationService.accepted(status));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [status]);

  async function transition(id, action, label) {
    if (!window.confirm(`${label} this donation?`)) return;
    try {
      await action(id);
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
          <h1>My accepted donations</h1>
        </div>
      </div>
      <div className="toolbar">
        <label>Status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All active history</option>
            <option value="ACCEPTED">ACCEPTED</option>
            <option value="COLLECTED">COLLECTED</option>
            <option value="DISTRIBUTED">DISTRIBUTED</option>
          </select>
        </label>
      </div>
      {error && <p className="alert error">{error}</p>}
      {loading ? <LoadingSpinner label="Loading accepted donations" /> : (
        <div className="list-stack">
          {donations.length ? donations.map((donation) => (
            <DonationCard key={donation.id} donation={donation} detailPath={`/receiver/donations/${donation.id}`}>
              {donation.status === "ACCEPTED" && (
                <button className="button" onClick={() => transition(donation.id, donationService.collect, "Mark collected")}>Collect</button>
              )}
              {donation.status === "COLLECTED" && (
                <button className="button" onClick={() => transition(donation.id, donationService.distribute, "Mark distributed")}>Distribute</button>
              )}
            </DonationCard>
          )) : <PageState title="No accepted donations found" message="Accept an available donation to start pickup work." />}
        </div>
      )}
    </section>
  );
}
