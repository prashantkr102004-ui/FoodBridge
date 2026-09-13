import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import NotificationBell from "./NotificationBell";
import { notificationService } from "../services/notificationService";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: "user-1", role: "DONOR" }
  })
}));

vi.mock("../services/notificationService", async () => {
  const actual = await vi.importActual("../services/notificationService");
  return {
    ...actual,
    notificationService: {
      unreadCount: vi.fn()
    }
  };
});

describe("NotificationBell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    notificationService.unreadCount.mockResolvedValue({ unread_count: 3 });
  });

  it("renders unread count for authenticated users", async () => {
    render(<MemoryRouter><NotificationBell /></MemoryRouter>);

    expect(await screen.findByText("3")).toBeInTheDocument();
    expect(screen.getByLabelText("Notifications, 3 unread")).toBeInTheDocument();
  });
});
