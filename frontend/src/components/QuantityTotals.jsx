export default function QuantityTotals({ totals = {} }) {
  const entries = Object.entries(totals || {});

  if (!entries.length) {
    return <p className="muted">No quantity totals yet.</p>;
  }

  return (
    <div className="quantity-list">
      {entries.map(([unit, value]) => (
        <span key={unit}>{Number(value).toLocaleString("en-IN")} {unit}</span>
      ))}
    </div>
  );
}
