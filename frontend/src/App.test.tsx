import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";
import { api } from "./api";
import type { Corridor, Plan, Route } from "./types";

vi.mock("./api", () => ({
  api: {
    health: vi.fn(),
    locations: vi.fn(),
    plan: vi.fn(),
    corridor: vi.fn(),
  },
}));
vi.mock("./components/RouteMap", () => ({
  default: () => <div data-testid="route-map" />,
}));
const route = (id: string): Route => ({
  id,
  name: `Route ${id}`,
  geometry: {
    type: "LineString",
    coordinates: [
      [-87, 41],
      [-83, 42],
    ],
  },
  distance_miles: 285,
  duration_seconds: 18000,
  arrival: "2026-10-24T16:00:00Z",
  checkpoints: [],
  segments: { type: "FeatureCollection", features: [] },
  summary: {
    miles_by_risk: {
      low: 240,
      moderate: 30,
      high: 15,
      severe: 0,
      no_travel: 0,
      unknown: 0,
    },
    average_risk: 0.2,
    eligible: true,
  },
});
const plan: Plan = {
  id: "plan-1",
  mode: "demo",
  generated_at: "2026-10-24T10:00:00Z",
  departure: "2026-10-24T11:00:00Z",
  timezone: "America/Chicago",
  load_lbs: 32000,
  spacing_miles: 25,
  routes: [route("A"), route("B"), route("C")],
  recommended_route_id: "A",
  recommendation_reason: "Route A has the lowest severe exposure.",
  warnings: [],
};
const corridor: Corridor = {
  plan_id: "plan-1",
  mode: "demo",
  start_time: "2026-10-24T11:00:00Z",
  hours: Array.from({ length: 49 }, (_, i) => i),
  resolution_miles: 25,
  geojson: { type: "FeatureCollection", features: [] },
  warnings: [],
};

beforeEach(() => {
  vi.mocked(api.health).mockResolvedValue({
    status: "ok",
    routing_configured: false,
  });
  vi.mocked(api.plan).mockResolvedValue(plan);
  vi.mocked(api.corridor).mockResolvedValue(corridor);
  vi.mocked(api.locations).mockResolvedValue({ locations: [] });
});

describe("trip planning state", () => {
  it("shows the recommended route first without changing backend route order", async () => {
    vi.mocked(api.plan).mockResolvedValue({
      ...plan,
      recommended_route_id: "C",
    });
    render(<App />);
    await screen.findByRole("button", { name: /Route C, recommended/ });
    const cards = screen.getAllByRole("button", { name: /^Route [ABC],/ });
    expect(cards[0]).toHaveAccessibleName(/Route C, recommended/);
    expect(cards[1]).toHaveAccessibleName(/^Route A,/);
    expect(cards[2]).toHaveAccessibleName(/^Route B,/);
    expect(plan.routes.map((route) => route.id)).toEqual(["A", "B", "C"]);
  });
  it("automatically loads the simulated demo with valid backend location IDs and selects the recommendation", async () => {
    render(<App />);
    expect(
      await screen.findByText("Route A has the lowest severe exposure."),
    ).toBeInTheDocument();
    expect(api.plan).toHaveBeenCalledWith(
      expect.objectContaining({
        mode: "demo",
        scenario: "mixed",
        origin: expect.objectContaining({ id: "demo-chicago" }),
        destination: expect.objectContaining({ id: "demo-detroit" }),
      }),
      expect.any(AbortSignal),
    );
    expect(
      screen.getByRole("button", { name: /Route A, recommended/ }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("DEMO · SIMULATED WEATHER")).toBeInTheDocument();
  });
  it("loads the corridor once and makes no network requests when moving the forecast slider", async () => {
    render(<App />);
    const slider = await screen.findByRole("slider", {
      name: "Forecast hours after departure",
    });
    fireEvent.change(slider, { target: { value: "36" } });
    expect(slider).toHaveValue("36");
    expect(api.corridor).toHaveBeenCalledTimes(1);
    expect(api.plan).toHaveBeenCalledTimes(1);
  });
  it("clears demo endpoint identities and shows configuration guidance when switching to live", async () => {
    render(<App />);
    await screen.findByText("Route A has the lowest severe exposure.");
    fireEvent.click(screen.getByRole("button", { name: "Live planning" }));
    expect(
      screen.getByRole("combobox", { name: "Starting point" }),
    ).toHaveValue("");
    expect(screen.getByRole("combobox", { name: "Destination" })).toHaveValue(
      "",
    );
    expect(
      screen.queryByText("Route A has the lowest severe exposure."),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Find safest routes" }),
    ).toBeDisabled();
    expect(
      screen.getByText(/Live routing needs a routing API key/),
    ).toBeInTheDocument();
  });
  it("ignores an old demo response after a mode switch even if the transport does not honor cancellation", async () => {
    let resolve!: (value: Plan) => void;
    vi.mocked(api.plan).mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r;
        }),
    );
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Live planning" }));
    await act(async () => {
      resolve(plan);
    });
    expect(
      screen.queryByText("Route A has the lowest severe exposure."),
    ).not.toBeInTheDocument();
    expect(api.corridor).not.toHaveBeenCalled();
  });
  it("preserves route results and exposes retry when corridor weather fails", async () => {
    vi.mocked(api.corridor).mockRejectedValue(
      new Error("Forecast provider unavailable."),
    );
    render(<App />);
    expect(
      await screen.findByText("Forecast provider unavailable."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Route A has the lowest severe exposure."),
    ).toBeInTheDocument();
    vi.mocked(api.corridor).mockResolvedValue(corridor);
    fireEvent.click(
      screen.getByRole("button", { name: "Retry corridor forecast" }),
    );
    await screen.findByRole("slider");
    expect(api.corridor).toHaveBeenCalledTimes(2);
  });
  it("shows no recommendation when all routes are ineligible", async () => {
    vi.mocked(api.plan).mockResolvedValue({
      ...plan,
      recommended_route_id: null,
      recommendation_reason:
        "No eligible route. All options contain no travel conditions.",
      routes: plan.routes.map((r) => ({
        ...r,
        summary: { ...r.summary, eligible: false },
      })),
    });
    render(<App />);
    await waitFor(() =>
      expect(
        screen.getByText(
          "No eligible route. All options contain no travel conditions.",
        ),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("RECOMMENDED ROUTE")).not.toBeInTheDocument();
    expect(screen.getAllByText("Ineligible")).toHaveLength(3);
  });
});
