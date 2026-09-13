import { Link } from "react-router-dom";
import { HeartHandshake, Leaf, ShieldCheck } from "lucide-react";

export default function Home() {
  return (
    <main className="home">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Smart surplus food donation</p>
          <h1>FoodBridge</h1>
          <p>
            Connect donors with NGOs and volunteers so edible surplus food can move from kitchens to people who need it.
          </p>
          <div className="hero-actions">
            <Link className="button" to="/register">Create account</Link>
            <Link className="button secondary" to="/login">Login</Link>
          </div>
        </div>
      </section>
      <section className="feature-grid">
        <article>
          <Leaf />
          <h2>Post surplus food</h2>
          <p>Donors can add available food with quantity, pickup address, and time details.</p>
        </article>
        <article>
          <HeartHandshake />
          <h2>Accept donations</h2>
          <p>NGOs and volunteers can find available food and move it through the pickup lifecycle.</p>
        </article>
        <article>
          <ShieldCheck />
          <h2>Role-based access</h2>
          <p>Each user sees only the actions that match their FoodBridge role.</p>
        </article>
      </section>
    </main>
  );
}
