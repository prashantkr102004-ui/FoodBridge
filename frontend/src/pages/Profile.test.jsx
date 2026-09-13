import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Profile from "./Profile";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "user-1",
      name: "Receiver",
      email: "receiver@example.com",
      phone: "9876543210",
      role: "NGO",
      organization_name: "Relief NGO",
      location: "Pune",
      latitude: null,
      longitude: null,
      is_active: true,
      created_at: "2026-09-07T00:00:00Z"
    },
    updateUser: vi.fn()
  })
}));

vi.mock("../services/authService", () => ({
  authService: {
    updateLocation: vi.fn(() =>
      Promise.resolve({
        id: "user-1",
        name: "Receiver",
        email: "receiver@example.com",
        phone: "9876543210",
        role: "NGO",
        organization_name: "Relief NGO",
        location: "Pune",
        latitude: null,
        longitude: null,
        is_active: true,
        created_at: "2026-09-07T00:00:00Z"
      })
    )
  }
}));

import { authService } from "../services/authService";

describe("Profile", () => {
  it("renders the location form", () => {
    render(<Profile />);

    expect(screen.getByText("Location for nearby matching")).toBeInTheDocument();
    expect(screen.queryByLabelText(/latitude/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/longitude/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /use my current location/i })).toBeInTheDocument();
  });

  it("saves address-only location without manual coordinates", async () => {
    const user = userEvent.setup();
    render(<Profile />);

    await user.click(screen.getByRole("button", { name: /save location/i }));

    expect(authService.updateLocation).toHaveBeenCalledWith({
      location: "Pune",
      latitude: null,
      longitude: null
    });
    expect(await screen.findByText("Location saved.")).toBeInTheDocument();
  });
});
