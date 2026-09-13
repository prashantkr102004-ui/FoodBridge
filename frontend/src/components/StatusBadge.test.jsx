import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import StatusBadge from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders known donation statuses", () => {
    render(<StatusBadge status="DISTRIBUTED" />);

    expect(screen.getByText("Distributed")).toBeInTheDocument();
  });
});
