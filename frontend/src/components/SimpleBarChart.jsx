export default function SimpleBarChart({ title, data = {}, valueLabel = (value) => value }) {
  const entries = Object.entries(data || {});
  const maxValue = Math.max(...entries.map(([, value]) => Number(value)), 0);

  return (
    <section className="panel">
      <h2>{title}</h2>
      {entries.length && maxValue > 0 ? (
        <div className="bar-list">
          {entries.map(([label, value]) => {
            const numericValue = Number(value);
            const width = maxValue ? Math.max(4, (numericValue / maxValue) * 100) : 0;
            return (
              <div className="bar-row" key={label}>
                <span>{label.replace("_", " ")}</span>
                <div className="bar-track" aria-label={`${label} ${valueLabel(numericValue)}`}>
                  <strong style={{ width: `${width}%` }} />
                </div>
                <b>{valueLabel(numericValue)}</b>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="muted">No data yet.</p>
      )}
    </section>
  );
}
