import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import Login from "./Login";
import { renderWithRoutes } from "../test/testUtils";

const loginMock = vi.fn();

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    login: loginMock,
    isAuthenticated: false,
    loading: false
  })
}));

describe("Login", () => {
  afterEach(() => {
    loginMock.mockReset();
  });

  it("logs in and navigates to the role home", async () => {
    loginMock.mockResolvedValue("/donor");
    const user = userEvent.setup();

    renderWithRoutes([
      { path: "/login", element: <Login /> },
      { path: "/donor", element: <p>Donor dashboard</p> }
    ], ["/login"]);

    await user.type(screen.getByLabelText(/email/i), "donor@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledWith({ email: "donor@example.com", password: "password123" }));
    expect(await screen.findByText("Donor dashboard")).toBeInTheDocument();
  });
});
