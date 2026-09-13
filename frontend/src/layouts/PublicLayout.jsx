import { Link, Outlet } from "react-router-dom";

export default function PublicLayout() {
  return (
    <div className="public-shell">
      <header className="public-nav">
        <Link className="brand" to="/">FoodBridge</Link>
        <div className="navlinks">
          <Link to="/login">Login</Link>
          <Link className="button small" to="/register">Create Account</Link>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
