import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SmartRecommendations from "./SmartRecommendations";
import { donationService } from "../services/donationService";
import { recommendationService } from "../services/recommendationService";

const recommendation = {
  id: "rec-1",
  food_name: "Veg Biryani",
  food_type: "VEGETARIAN",
  quantity: 50,
  quantity_unit: "MEALS",
  description: "Packed boxes",
  pickup_address: "College Canteen",
  latitude: 18.52,
  longitude: 73.85,
  available_until: "2030-01-01T10:00:00Z",
  status: "AVAILABLE",
  distance_km: 1.84,
  match_score: 92,
  score_breakdown: {
    distance: 96,
    urgency: 90,
    quantity: 80,
    preference: 88
  },
  reasons: ["Only 1.8 km away", "Expires within 60 minutes", "Large available quantity"]
};

vi.mock("../services/recommendationService", () => ({
  recommendationService: {
    donations: vi.fn()
  }
}));

vi.mock("../services/donationService", () => ({
  donationService: {
    accept: vi.fn()
  }
}));

describe("SmartRecommendations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    recommendationService.donations.mockResolvedValue([recommendation]);
    donationService.accept.mockResolvedValue({});
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("renders match scores and recommendation reasons", async () => {
    render(<MemoryRouter><SmartRecommendations /></MemoryRouter>);

    expect(await screen.findByText("Veg Biryani")).toBeInTheDocument();
    expect(screen.getByText("92/100")).toBeInTheDocument();
    expect(screen.getByText("Only 1.8 km away")).toBeInTheDocument();
    expect(screen.getByText("Distance")).toBeInTheDocument();
  });

  it("shows a no-location error", async () => {
    recommendationService.donations.mockRejectedValueOnce({
      response: { data: { detail: "Set your location before using smart recommendations." }, status: 400 }
    });

    render(<MemoryRouter><SmartRecommendations /></MemoryRouter>);

    expect(await screen.findByText("Set your location before using smart recommendations.")).toBeInTheDocument();
  });

  it("shows an empty recommendation state", async () => {
    recommendationService.donations.mockResolvedValueOnce([]);

    render(<MemoryRouter><SmartRecommendations /></MemoryRouter>);

    expect(await screen.findByText("No recommendations found")).toBeInTheDocument();
  });

  it("accepts a recommendation and refreshes the list", async () => {
    recommendationService.donations.mockResolvedValueOnce([recommendation]).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    render(<MemoryRouter><SmartRecommendations /></MemoryRouter>);

    await screen.findByText("Veg Biryani");
    await user.click(screen.getByRole("button", { name: "Accept Donation" }));

    await waitFor(() => expect(donationService.accept).toHaveBeenCalledWith("rec-1"));
    await waitFor(() => expect(screen.getByText("No recommendations found")).toBeInTheDocument());
  });
});
