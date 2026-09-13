export default function MonthlyActivity({ items = [] }) {
  const maxValue = Math.max(...items.flatMap((item) => [item.created || 0, item.distributed || 0]), 0);

  return (
    <section className="panel">
      <h2>Monthly activity</h2>
      {items.length && maxValue > 0 ? (
        <div className="monthly-chart">
          {items.map((item) => (
            <div className="month-group" key={item.month}>
              <div className="month-bars">
                <span
                  className="created"
                  style={{ height: `${maxValue ? Math.max(6, (item.created / maxValue) * 100) : 0}%` }}
                  title={`${item.created} created`}
                />
                <span
                  className="distributed"
                  style={{ height: `${maxValue ? Math.max(6, (item.distributed / maxValue) * 100) : 0}%` }}
                  title={`${item.distributed} distributed`}
                />
              </div>
              <strong>{item.month}</strong>
              <small>{item.created} created / {item.distributed} distributed</small>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">No donation activity yet.</p>
      )}
    </section>
  );
}
