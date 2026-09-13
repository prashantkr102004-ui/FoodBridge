export default function PageState({ title, message, children }) {
  return (
    <section className="page-state">
      <h2>{title}</h2>
      {message && <p className="muted">{message}</p>}
      {children}
    </section>
  );
}
