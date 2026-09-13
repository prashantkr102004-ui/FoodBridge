import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Notifications from "./Notifications";
import { notificationService } from "../services/notificationService";

const unreadNotification = {
  id: "note-1",
  type: "DONATION_ACCEPTED",
  title: "Donation Accepted",
  message: "Your donation 'Veg Biryani' was accepted by Hope NGO.",
  donation_id: "donation-1",
  is_read: false,
  created_at: "2030-01-01T10:00:00Z",
  read_at: null
};

const readNotification = {
  id: "note-2",
  type: "DONATION_COLLECTED",
  title: "Food Collected",
  message: "Your donation has been collected.",
  donation_id: null,
  is_read: true,
  created_at: "2030-01-01T09:00:00Z",
  read_at: "2030-01-01T09:05:00Z"
};

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: "user-1", role: "DONOR" }
  })
}));

vi.mock("../services/notificationService", () => ({
  notificationService: {
    list: vi.fn(),
    markRead: vi.fn(),
    markAllRead: vi.fn()
  }
}));

describe("Notifications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    notificationService.list.mockResolvedValue({
      total: 2,
      page: 1,
      page_size: 20,
      items: [unreadNotification, readNotification]
    });
    notificationService.markRead.mockResolvedValue({ ...unreadNotification, is_read: true, read_at: "2030-01-01T10:05:00Z" });
    notificationService.markAllRead.mockResolvedValue({ updated: 1 });
  });

  it("renders notification items with unread distinction", async () => {
    render(<MemoryRouter><Notifications /></MemoryRouter>);

    expect(await screen.findByText("Donation Accepted")).toBeInTheDocument();
    expect(screen.getByText("Unread")).toBeInTheDocument();
    expect(screen.getByText("Your donation 'Veg Biryani' was accepted by Hope NGO.")).toBeInTheDocument();
  });

  it("marks one notification read", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><Notifications /></MemoryRouter>);

    await screen.findByText("Donation Accepted");
    await user.click(screen.getByRole("button", { name: "Mark read" }));

    await waitFor(() => expect(notificationService.markRead).toHaveBeenCalledWith("note-1"));
  });

  it("marks all notifications read", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><Notifications /></MemoryRouter>);

    await screen.findByText("Donation Accepted");
    await user.click(screen.getByRole("button", { name: "Mark all as read" }));

    await waitFor(() => expect(notificationService.markAllRead).toHaveBeenCalled());
  });

  it("renders empty state", async () => {
    notificationService.list.mockResolvedValueOnce({ total: 0, page: 1, page_size: 20, items: [] });

    render(<MemoryRouter><Notifications /></MemoryRouter>);

    expect(await screen.findByText("No notifications yet.")).toBeInTheDocument();
  });

  it("links notification donations to the donor detail page", async () => {
    render(<MemoryRouter><Notifications /></MemoryRouter>);

    expect(await screen.findByRole("link", { name: "Open donation" })).toHaveAttribute("href", "/donor/donations/donation-1");
  });
});
