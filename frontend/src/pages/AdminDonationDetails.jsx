import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LifecycleTimeline from "../components/LifecycleTimeline";
import LoadingSpinner from "../components/LoadingSpinner";
import PageState from "../components/PageState";
import StatusBadge from "../components/StatusBadge";
import { adminService } from "../services/adminService";
import { formatDate, formatQuantity } from "../utils/format";
import { getMediaUrl } from "../utils/media";

export default function AdminDonationDetails() {
  const { id } = useParams();
  const [donation, setDonation] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    adminService.donation(id).then(setDonation).catch((err) => setError(getApiErrorMessage(err)));
  }, [id]);

  if (error) return <PageState title="Donation unavailable" message={error} />;
  if (!donation) return <LoadingSpinner label="Loading donation" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Admin donation</p>
          <h1>{donation.food_name}</h1>
        </div>
        <StatusBadge status={donation.status} />
      </div>
      <div className="details-layout">
        <article className="panel">
          {donation.image_url && <img className="donation-image" src={getMediaUrl(donation.image_url)} alt={donation.food_name} />}
          <dl className="details-grid">
            <div><span>Food type</span><strong>{donation.food_type.replace("_", " ")}</strong></div>
            <div><span>Quantity</span><strong>{formatQuantity(donation.quantity, donation.quantity_unit)}</strong></div>
            <div><span>Donor ID</span><strong>{donation.donor_id}</strong></div>
            <div><span>Accepted by ID</span><strong>{donation.accepted_by_user_id || "Not accepted"}</strong></div>
            <div><span>Prepared at</span><strong>{formatDate(donation.prepared_at)}</strong></div>
            <div><span>Available until</span><strong>{formatDate(donation.available_until)}</strong></div>
            <div><span>Pickup address</span><strong>{donation.pickup_address}</strong></div>
            <div><span>Description</span><strong>{donation.description || "Not provided"}</strong></div>
          </dl>
        </article>
        <aside className="panel">
          <h2>Lifecycle timestamps</h2>
          <LifecycleTimeline donation={donation} />
        </aside>
      </div>
    </section>
  );
}
