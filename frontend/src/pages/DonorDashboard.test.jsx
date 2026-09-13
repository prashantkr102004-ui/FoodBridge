import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import DonorDashboard from "./DonorDashboard";

vi.mock("../services/dashboardService", () => ({
  dashboardService: {
    donor: vi.fn().mockResolvedValue({
      total_donations: 3,
      available_donations: 1,
      accepted_donations: 1,
      collected_donations: 0,
      distributed_donations: 1,
      cancelled_donations: 0,
      expired_donations: 0,
      total_quantity_donated: { MEALS: 25 },
      recent_donations: [
        {
          id: 1,
          food_name: "Rice meals",
          food_type: "VEGETARIAN",
          quantity: 25,
          quantity_unit: "MEALS",
          status: "AVAILABLE",
          available_until: "2030-01-01T10:00:00Z",
          pickup_address: "Campus gate"
        }
      ]
    })
  }
}));

describe("DonorDashboard", () => {
  it("renders donor dashboard API data", async () => {
    render(<MemoryRouter><DonorDashboard /></MemoryRouter>);

    expect(await screen.findByText("Your donation summary")).toBeInTheDocument();
    expect(screen.getByText("Rice meals")).toBeInTheDocument();
    expect(screen.getByText("25 MEALS")).toBeInTheDocument();
  });
});
