import { Link } from "react-router-dom";

export default function NotFound({ message = "The page you requested was not found." }) {
  return (
    <section className="page-state">
      <h1>Not available</h1>
      <p className="muted">{message}</p>
      <Link className="button" to="/">Go home</Link>
    </section>
  );
}
