const statusLabels = {
  AVAILABLE: "Available",
  ACCEPTED: "Accepted",
  COLLECTED: "Collected",
  DISTRIBUTED: "Distributed",
  CANCELLED: "Cancelled",
  EXPIRED: "Expired"
};

export default function StatusBadge({ status }) {
  return <span className={`status status-${status}`}>{statusLabels[status] || status}</span>;
}
