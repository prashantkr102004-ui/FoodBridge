import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LifecycleTimeline from "../components/LifecycleTimeline";
import LoadingSpinner from "../components/LoadingSpinner";
import { DonationMap } from "../components/MapView";
import PageState from "../components/PageState";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../context/AuthContext";
import { donationService } from "../services/donationService";
import { formatDate, formatQuantity } from "../utils/format";
import { getMediaUrl } from "../utils/media";

export default function DonationDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const [donation, setDonation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setDonation(await donationService.detail(id));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function runAction(label, action) {
    if (!window.confirm(`${label} this donation?`)) return;
    setActionError("");
    try {
      setDonation(await action(id));
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    }
  }

  if (loading) return <LoadingSpinner label="Loading donation details" />;
  if (error) return <PageState title="Donation unavailable" message={error} />;
  if (!donation) return null;

  const isReceiver = user.role === "NGO" || user.role === "VOLUNTEER";
  const isDonor = user.role === "DONOR";

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Donation details</p>
          <h1>{donation.food_name}</h1>
        </div>
        <StatusBadge status={donation.status} />
      </div>
      {actionError && <p className="alert error">{actionError}</p>}
      <div className="details-layout">
        <article className="panel">
          {donation.image_url && <img className="donation-image" src={getMediaUrl(donation.image_url)} alt={donation.food_name} />}
          <dl className="details-grid">
            <div><span>Food type</span><strong>{donation.food_type.replace("_", " ")}</strong></div>
            <div><span>Quantity</span><strong>{formatQuantity(donation.quantity, donation.quantity_unit)}</strong></div>
            <div><span>Prepared at</span><strong>{formatDate(donation.prepared_at)}</strong></div>
            <div><span>Available until</span><strong>{formatDate(donation.available_until)}</strong></div>
            <div><span>Pickup address</span><strong>{donation.pickup_address}</strong></div>
            {donation.latitude !== null && donation.latitude !== undefined && <div><span>Latitude</span><strong>{donation.latitude}</strong></div>}
            {donation.longitude !== null && donation.longitude !== undefined && <div><span>Longitude</span><strong>{donation.longitude}</strong></div>}
            <div><span>Description</span><strong>{donation.description || "Not provided"}</strong></div>
            {donation.donor_name && <div><span>Donor</span><strong>{donation.donor_organization_name || donation.donor_name}</strong></div>}
            {donation.donor_phone && <div><span>Donor phone</span><strong>{donation.donor_phone}</strong></div>}
            {donation.accepted_by_name && <div><span>Accepted by</span><strong>{donation.accepted_by_organization_name || donation.accepted_by_name}</strong></div>}
          </dl>
          <DonationMap donation={donation} />
        </article>
        <aside className="panel">
          <h2>Lifecycle</h2>
          <LifecycleTimeline donation={donation} />
          <div className="actions vertical">
            {isDonor && donation.status === "AVAILABLE" && (
              <>
                <Link className="button secondary" to={`/donor/donations/${donation.id}/edit`}>Edit</Link>
                <button className="button danger" onClick={() => runAction("Cancel", donationService.cancel)}>Cancel</button>
              </>
            )}
            {isReceiver && donation.status === "AVAILABLE" && (
              <button className="button" onClick={() => runAction("Accept", donationService.accept)}>Accept donation</button>
            )}
            {isReceiver && donation.status === "ACCEPTED" && (
              <button className="button" onClick={() => runAction("Mark collected", donationService.collect)}>Mark collected</button>
            )}
            {isReceiver && donation.status === "COLLECTED" && (
              <button className="button" onClick={() => runAction("Mark distributed", donationService.distribute)}>Mark distributed</button>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
