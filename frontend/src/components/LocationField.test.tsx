import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import LocationField from "./LocationField";
import { api } from "../api";
import { CHICAGO, DETROIT } from "../utils";
import type { Location } from "../types";

vi.mock("../api", () => ({ api: { locations: vi.fn() } }));
function Harness() {
  const [value, setValue] = useState<Location | null>(CHICAGO);
  return (
    <LocationField
      label="Origin"
      value={value}
      mode="demo"
      onChange={setValue}
    />
  );
}

describe("location selection", () => {
  it("preserves typed text while invalidating the previous selection and supports keyboard selection", async () => {
    vi.mocked(api.locations).mockResolvedValue({ locations: [DETROIT] });
    render(<Harness />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "Detr" } });
    expect(input).toHaveValue("Detr");
    await screen.findByRole("option", { name: /Detroit/ });
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(input).toHaveValue("Detroit, MI");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });
});
