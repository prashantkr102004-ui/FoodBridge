import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import DonationForm from "./DonationForm";
import { renderWithRoutes } from "../test/testUtils";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { location: "Pune Canteen", latitude: null, longitude: null }
  })
}));

const originalMediaDevices = navigator.mediaDevices;

afterEach(() => {
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: originalMediaDevices
  });
});

describe("DonationForm", () => {
  it("shows validation when required fields are missing", async () => {
    const user = userEvent.setup();

    renderWithRoutes([{ path: "/donor/post", element: <DonationForm mode="create" /> }], ["/donor/post"]);

    await user.click(screen.getByRole("button", { name: /save donation/i }));

    expect(await screen.findByText("Food name is required.")).toBeInTheDocument();
  });

  it("defaults quantity to 0.5 KG and hides coordinate fields", () => {
    renderWithRoutes([{ path: "/donor/post", element: <DonationForm mode="create" /> }], ["/donor/post"]);

    expect(screen.getByLabelText(/quantity/i)).toHaveValue(0.5);
    expect(screen.getByLabelText(/unit/i)).toHaveValue("KG");
    expect(screen.getByLabelText(/pickup address/i)).toHaveValue("Pune Canteen");
    expect(screen.queryByLabelText(/pickup latitude/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/pickup longitude/i)).not.toBeInTheDocument();
    expect(screen.getByText(/add picture/i)).toBeInTheDocument();
    expect(screen.getByText(/click picture/i)).toBeInTheDocument();
  });

  it("requests camera permission when Click picture is selected", async () => {
    const user = userEvent.setup();
    const getUserMedia = vi.fn(() => Promise.resolve({
      getTracks: () => [{ stop: vi.fn() }]
    }));
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia }
    });

    renderWithRoutes([{ path: "/donor/post", element: <DonationForm mode="create" /> }], ["/donor/post"]);

    await user.click(screen.getByRole("button", { name: /click picture/i }));

    expect(getUserMedia).toHaveBeenCalledWith({ video: { facingMode: "environment" } });
    expect(await screen.findByRole("button", { name: /capture photo/i })).toBeInTheDocument();
  });
});
