import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function DashboardLayout() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}
