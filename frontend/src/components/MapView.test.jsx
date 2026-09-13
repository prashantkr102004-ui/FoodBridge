import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { DonationMap, NearbyDonationsMap } from "./MapView";

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }) => <div data-testid="leaflet-map">{children}</div>,
  TileLayer: () => <div />,
  Marker: ({ children }) => <div>{children}</div>,
  Popup: ({ children }) => <div>{children}</div>
}));

describe("map views", () => {
  it("does not render a donation map when coordinates are absent", () => {
    render(<DonationMap donation={{ food_name: "Rice", pickup_address: "Pune", latitude: null, longitude: null }} />);

    expect(screen.queryByTestId("pickup-map")).not.toBeInTheDocument();
  });

  it("renders a donation map when valid coordinates exist", () => {
    render(<DonationMap donation={{ food_name: "Rice", pickup_address: "Pune", latitude: 18.52, longitude: 73.85 }} />);

    expect(screen.getByTestId("pickup-map")).toBeInTheDocument();
  });

  it("renders nearby donation markers when user and donation coordinates exist", () => {
    render(
      <MemoryRouter>
        <NearbyDonationsMap
          user={{ latitude: 18.52, longitude: 73.85 }}
          donations={[{ id: "1", food_name: "Meals", quantity: 20, quantity_unit: "MEALS", distance_km: 2.44, latitude: 18.53, longitude: 73.86 }]}
        />
      </MemoryRouter>
    );

    expect(screen.getByTestId("nearby-map")).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes("Approx. 2.4 km away"))).toBeInTheDocument();
  });
});
