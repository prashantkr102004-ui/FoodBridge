import { afterEach, describe, expect, it, vi } from "vitest";
import apiClient from "./client";

const originalAdapter = apiClient.defaults.adapter;

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter;
  vi.restoreAllMocks();
});

describe("api client", () => {
  it("dispatches unauthorized when the backend rejects a deactivated account", async () => {
    const listener = vi.fn();
    window.addEventListener("foodbridge:unauthorized", listener);
    apiClient.defaults.adapter = () =>
      Promise.reject({
        response: {
          status: 403,
          data: { detail: "This account is deactivated" }
        }
      });

    await expect(apiClient.get("/protected")).rejects.toBeTruthy();

    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener("foodbridge:unauthorized", listener);
  });
});
