import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { roleHome } from "../utils/format";

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading, user } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loginRole, setLoginRole] = useState("DONOR");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && isAuthenticated && user) return <Navigate to={roleHome(user.role)} replace />;

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const home = await login(form);
      navigate(home, { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-page">
      <div>
        <p className="eyebrow">Welcome back</p>
        <h1>Login to FoodBridge</h1>
        <p className="muted">Choose how you are using FoodBridge today, then login with your account.</p>
      </div>
      <form className="form-panel" onSubmit={handleSubmit}>
        {error && <p className="alert error">{error}</p>}
        <div>
          <span className="field-label">I am logging in as</span>
          <div className="account-choice">
            <button
              className={loginRole === "DONOR" ? "active" : ""}
              type="button"
              onClick={() => setLoginRole("DONOR")}
            >
              Donor
            </button>
            <button
              className={loginRole === "RECEIVER" ? "active" : ""}
              type="button"
              onClick={() => setLoginRole("RECEIVER")}
            >
              NGO / Accepter
            </button>
          </div>
          <p className="muted small-note">
            {loginRole === "DONOR"
              ? "Use this if you post surplus food."
              : "Use this if you accept, collect, or distribute food donations."}
          </p>
        </div>
        <label>Email
          <input name="email" type="email" value={form.email} onChange={updateField} required />
        </label>
        <label>Password
          <input name="password" type="password" value={form.password} onChange={updateField} required />
        </label>
        <button className="button" disabled={submitting}>{submitting ? "Logging in..." : "Login"}</button>
        <p className="muted">
          New here? <Link to={`/register?role=${loginRole === "DONOR" ? "DONOR" : "NGO"}`}>Create an account</Link>
        </p>
      </form>
    </section>
  );
}
