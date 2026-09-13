import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { roleHome } from "../utils/format";

export default function RoleRoute({ allowedRoles }) {
  const { user } = useAuth();
  if (!user) return null;
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={roleHome(user.role)} replace />;
  }
  return <Outlet />;
}
