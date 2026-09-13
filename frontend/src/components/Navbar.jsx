import { LogOut, UtensilsCrossed } from "lucide-react";
import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";

const linksByRole = {
  DONOR: [
    ["Dashboard", "/donor"],
    ["Impact", "/donor/impact"],
    ["Post Donation", "/donor/post"],
    ["My Donations", "/donor/donations"],
    ["Profile", "/profile"]
  ],
  NGO: [
    ["Dashboard", "/receiver"],
    ["Impact", "/receiver/impact"],
    ["Available Food", "/receiver/available"],
    ["Smart Recommendations", "/receiver/recommendations"],
    ["My Accepted", "/receiver/accepted"],
    ["Profile", "/profile"]
  ],
  VOLUNTEER: [
    ["Dashboard", "/receiver"],
    ["Impact", "/receiver/impact"],
    ["Available Food", "/receiver/available"],
    ["Smart Recommendations", "/receiver/recommendations"],
    ["My Accepted", "/receiver/accepted"],
    ["Profile", "/profile"]
  ],
  ADMIN: [
    ["Dashboard", "/admin"],
    ["Analytics", "/admin/analytics"],
    ["Users", "/admin/users"],
    ["Donations", "/admin/donations"]
  ]
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const links = user ? linksByRole[user.role] || [] : [];

  return (
    <header className="topbar">
      <Link className="brand" to="/">
        <UtensilsCrossed size={24} aria-hidden="true" />
        <span>FoodBridge</span>
      </Link>
      <nav className="navlinks" aria-label="Main navigation">
        {links.map(([label, href]) => (
          <NavLink key={href} to={href} end={href === "/donor" || href === "/receiver" || href === "/admin"}>
            {label}
          </NavLink>
        ))}
      </nav>
      {user && (
        <div className="topbar-actions">
          <NotificationBell />
          <button className="icon-button" type="button" onClick={logout} title="Logout" aria-label="Logout">
            <LogOut size={18} aria-hidden="true" />
            <span>Logout</span>
          </button>
        </div>
      )}
    </header>
  );
}
