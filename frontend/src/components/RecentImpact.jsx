import { formatDate, formatQuantity } from "../utils/format";

export default function RecentImpact({ items = [] }) {
  return (
    <section className="panel">
      <h2>Recent impact</h2>
      {items.length ? (
        <div className="list-stack">
          {items.map((item) => (
            <article className="impact-item" key={item.id}>
              <strong>{formatQuantity(item.quantity, item.quantity_unit)} distributed</strong>
              <span>{item.food_name}</span>
              <small>{formatDate(item.distributed_at)}</small>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">No completed impact yet.</p>
      )}
    </section>
  );
}
