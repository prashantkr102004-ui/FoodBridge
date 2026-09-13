import { formatDate } from "../utils/format";

const steps = [
  ["Posted", "created_at"],
  ["Accepted", "accepted_at"],
  ["Collected", "collected_at"],
  ["Distributed", "distributed_at"]
];

export default function LifecycleTimeline({ donation }) {
  return (
    <ol className="timeline">
      {steps.map(([label, key]) => (
        <li key={key} className={donation[key] ? "complete" : ""}>
          <span>{label}</span>
          <small>{formatDate(donation[key])}</small>
        </li>
      ))}
    </ol>
  );
}
