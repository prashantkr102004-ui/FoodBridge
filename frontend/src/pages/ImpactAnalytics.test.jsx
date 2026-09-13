import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RoleRoute from "../components/RoleRoute";
import { renderWithRoutes } from "../test/testUtils";
import AdminAnalytics from "./AdminAnalytics";
import DonorImpact from "./DonorImpact";
import ReceiverImpact from "./ReceiverImpact";
import { analyticsService } from "../services/analyticsService";
import { useAuth } from "../context/AuthContext";

vi.mock("../context/AuthContext", () => ({
  useAuth: vi.fn()
}));

vi.mock("../services/analyticsService", () => ({
  analyticsService: {
    donor: vi.fn(),
    receiver: vi.fn(),
    admin: vi.fn(),
    exportCsv: vi.fn()
  }
}));

const monthly = [{ month: "2026-09", created: 2, distributed: 1 }];

describe("impact analytics pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({ isAuthenticated: true, loading: false, user: { role: "DONOR" } });
    analyticsService.donor.mockResolvedValue({
      total_donations: 3,
      distributed_donations: 2,
      active_donations: 1,
      cancelled_donations: 0,
      expired_donations: 0,
      success_rate: 100,
      quantity_by_unit: { MEALS: 30, KG: 5 },
      distributed_quantity_by_unit: { MEALS: 20, KG: 5 },
      food_type_breakdown: { VEGETARIAN: 2, VEGAN: 1 },
      monthly_activity: monthly,
      recent_impact: [{ id: "1", food_name: "Rice", quantity: 20, quantity_unit: "MEALS", distributed_at: "2030-01-01" }]
    });
    analyticsService.receiver.mockResolvedValue({
      total_accepted: 2,
      currently_accepted: 0,
      collected: 1,
      distributed: 1,
      completion_rate: 50,
      quantity_rescued_by_unit: { PACKETS: 12 },
      food_type_breakdown: { VEGETARIAN: 1 },
      monthly_activity: monthly,
      recent_impact: []
    });
    analyticsService.admin.mockResolvedValue({
      total_users: 5,
      total_donations: 4,
      total_distributed: 2,
      total_cancelled: 1,
      total_expired: 1,
      distribution_success_rate: 50,
      users_by_role: { DONOR: 2, NGO: 1, VOLUNTEER: 1, ADMIN: 1 },
      donations_by_status: { DISTRIBUTED: 2, CANCELLED: 1, EXPIRED: 1 },
      quantity_distributed_by_unit: { MEALS: 40, KG: 6 },
      food_type_breakdown: { VEGETARIAN: 3 },
      monthly_donation_activity: monthly
    });
    analyticsService.exportCsv.mockResolvedValue(new Blob(["Donation ID,Food Name"], { type: "text/csv" }));
    global.URL.createObjectURL = vi.fn(() => "blob:foodbridge-report");
    global.URL.revokeObjectURL = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  it("renders donor impact with separated quantity units", async () => {
    render(<MemoryRouter><DonorImpact /></MemoryRouter>);

    expect(await screen.findByText("Your food impact")).toBeInTheDocument();
    expect(screen.getAllByText("20 MEALS").length).toBeGreaterThan(0);
    expect(screen.getAllByText("5 KG").length).toBeGreaterThan(0);
  });

  it("renders receiver impact", async () => {
    render(<MemoryRouter><ReceiverImpact /></MemoryRouter>);

    expect(await screen.findByText("Food rescued by you")).toBeInTheDocument();
    expect(screen.getByText("12 PACKETS")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("renders admin analytics and chart sections", async () => {
    render(<MemoryRouter><AdminAnalytics /></MemoryRouter>);

    expect(await screen.findByText("Platform impact")).toBeInTheDocument();
    expect(screen.getByText("Donation status breakdown")).toBeInTheDocument();
    expect(screen.getByText("Monthly activity")).toBeInTheDocument();
  });

  it("renders zero-data analytics safely", async () => {
    analyticsService.admin.mockResolvedValueOnce({
      total_users: 1,
      total_donations: 0,
      total_distributed: 0,
      total_cancelled: 0,
      total_expired: 0,
      distribution_success_rate: 0,
      users_by_role: {},
      donations_by_status: {},
      quantity_distributed_by_unit: {},
      food_type_breakdown: {},
      monthly_donation_activity: [{ month: "2026-09", created: 0, distributed: 0 }]
    });

    render(<MemoryRouter><AdminAnalytics /></MemoryRouter>);

    expect(await screen.findByText("Platform impact")).toBeInTheDocument();
    expect(screen.getAllByText("No data yet.").length).toBeGreaterThan(0);
    expect(screen.getByText("No donation activity yet.")).toBeInTheDocument();
  });

  it("exports CSV from admin analytics", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><AdminAnalytics /></MemoryRouter>);

    await screen.findByText("Platform impact");
    await user.click(screen.getByRole("button", { name: "Export CSV" }));

    await waitFor(() => expect(analyticsService.exportCsv).toHaveBeenCalled());
    expect(await screen.findByText("CSV export ready.")).toBeInTheDocument();
  });

  it("wrong role cannot access analytics route", () => {
    useAuth.mockReturnValue({ isAuthenticated: true, loading: false, user: { role: "NGO" } });

    renderWithRoutes([
      <Route key="role" element={<RoleRoute allowedRoles={["DONOR"]} />}>
        <Route path="/donor/impact" element={<p>Donor impact route</p>} />
      </Route>,
      <Route key="receiver" path="/receiver" element={<p>Receiver page</p>} />
    ], ["/donor/impact"]);

    expect(screen.getByText("Receiver page")).toBeInTheDocument();
  });
});
