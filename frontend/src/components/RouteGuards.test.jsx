import { Route } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import ProtectedRoute from "./ProtectedRoute";
import RoleRoute from "./RoleRoute";
import { renderWithRoutes } from "../test/testUtils";

vi.mock("../context/AuthContext", () => ({
  useAuth: vi.fn()
}));

import { useAuth } from "../context/AuthContext";

describe("route guards", () => {
  it("redirects logged-out users away from protected pages", () => {
    useAuth.mockReturnValue({ isAuthenticated: false, loading: false, user: null });

    renderWithRoutes([
      <Route key="protected" element={<ProtectedRoute />}>
        <Route path="/notifications" element={<p>Notifications page</p>} />
      </Route>,
      <Route key="login" path="/login" element={<p>Login page</p>} />
    ], ["/notifications"]);

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects users away from routes for another role", () => {
    useAuth.mockReturnValue({ isAuthenticated: true, loading: false, user: { role: "NGO" } });

    renderWithRoutes([
      <Route key="role" element={<RoleRoute allowedRoles={["DONOR"]} />}>
        <Route path="/donor" element={<p>Donor page</p>} />
      </Route>,
      <Route key="receiver" path="/receiver" element={<p>Receiver page</p>} />
    ], ["/donor"]);

    expect(screen.getByText("Receiver page")).toBeInTheDocument();
  });
});
