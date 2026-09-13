import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import AvailableFood from "./AvailableFood";
import { donationService } from "../services/donationService";

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }) => <div data-testid="leaflet-map">{children}</div>,
  TileLayer: () => <div />,
  Marker: ({ children }) => <div>{children}</div>,
  Popup: ({ children }) => <div>{children}</div>
}));

vi.mock("../services/donationService", () => ({
  donationService: {
    available: vi.fn().mockResolvedValue([
      {
        id: 10,
        food_name: "Fresh chapati",
        food_type: "VEGETARIAN",
        quantity: 40,
        quantity_unit: "MEALS",
        description: "Packed and ready",
        status: "AVAILABLE",
        available_until: "2030-01-01T10:00:00Z",
        pickup_address: "Hotel kitchen"
      }
    ]),
    nearby: vi.fn().mockResolvedValue([
      {
        id: 11,
        food_name: "Nearby rice",
        food_type: "VEGETARIAN",
        quantity: 15,
        quantity_unit: "MEALS",
        status: "AVAILABLE",
        pickup_address: "Nearby kitchen",
        available_until: "2030-01-01T10:00:00Z",
        latitude: 18.52,
        longitude: 73.85,
        distance_km: 2.42
      }
    ]),
    accept: vi.fn()
  }
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "NGO", latitude: 18.52, longitude: 73.85 }
  })
}));

describe("AvailableFood", () => {
  it("renders available donations for receivers", async () => {
    render(<MemoryRouter><AvailableFood /></MemoryRouter>);

    expect(await screen.findByText("Fresh chapati")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept" })).toBeInTheDocument();
  });

  it("renders nearby donations with distance", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><AvailableFood /></MemoryRouter>);

    await user.click(screen.getByRole("button", { name: "Nearby Food" }));

    expect((await screen.findAllByText("Nearby rice")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Approx. 2.4 km away").length).toBeGreaterThan(0);
  });

  it("shows a missing location error from the nearby API", async () => {
    donationService.nearby.mockRejectedValueOnce({
      response: { data: { detail: "Set your location before using nearby donations." }, status: 400 }
    });
    const user = userEvent.setup();
    render(<MemoryRouter><AvailableFood /></MemoryRouter>);

    await user.click(screen.getByRole("button", { name: "Nearby Food" }));

    expect(await screen.findByText("Set your location before using nearby donations.")).toBeInTheDocument();
  });
});
