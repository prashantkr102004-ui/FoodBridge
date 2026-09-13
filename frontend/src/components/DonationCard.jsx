import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import { formatDate, formatQuantity } from "../utils/format";

export default function DonationCard({ donation, detailPath, children }) {
  const hasPickupDetails = donation.available_until || donation.pickup_address;

  return (
    <article className="donation-card">
      <div>
        <div className="row-between">
          <h3>{donation.food_name}</h3>
          <StatusBadge status={donation.status} />
        </div>
        <p className="muted">{donation.food_type.replace("_", " ")} - {formatQuantity(donation.quantity, donation.quantity_unit)}</p>
        {donation.description && <p>{donation.description}</p>}
        {hasPickupDetails && (
          <dl className="mini-grid">
            {donation.available_until && <div><dt>Available until</dt><dd>{formatDate(donation.available_until)}</dd></div>}
            {donation.pickup_address && <div><dt>Pickup</dt><dd>{donation.pickup_address}</dd></div>}
          </dl>
        )}
      </div>
      <div className="actions">
        {detailPath && <Link className="button secondary" to={detailPath}>View</Link>}
        {children}
      </div>
    </article>
  );
}
