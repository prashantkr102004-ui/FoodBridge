import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Navbar from "./Navbar";

const logoutMock = vi.fn();

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: "user-1", role: "DONOR", name: "Donor User" },
    logout: logoutMock
  })
}));

vi.mock("../services/notificationService", async () => {
  const actual = await vi.importActual("../services/notificationService");
  return {
    ...actual,
    notificationService: {
      unreadCount: vi.fn().mockResolvedValue({ unread_count: 0 })
    }
  };
});

describe("Navbar", () => {
  it("calls logout when the logout button is clicked", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><Navbar /></MemoryRouter>);

    await user.click(screen.getByRole("button", { name: /logout/i }));

    expect(logoutMock).toHaveBeenCalled();
  });
});
