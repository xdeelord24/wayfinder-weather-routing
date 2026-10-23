import type { FeatureCollection, LineString, Polygon } from "geojson";

export type Risk =
  "low" | "moderate" | "high" | "severe" | "no_travel" | "unknown";
export type Mode = "demo" | "live";
export type Scenario = "mixed" | "blocked" | "clear";
export interface Location {
  id: string;
  label: string;
  lat: number;
  lon: number;
  timezone: string;
}
export interface Weather {
  wind_mph: number;
  rain_in_hr: number;
  snow_in_hr: number;
  forecast_time: string;
}
export interface Checkpoint {
  id: string;
  lat: number;
  lon: number;
  distance_miles: number;
  eta: string;
  weather: Weather | null;
  risk: Risk;
  reasons: string[];
  exposure_miles: number;
}
export interface Route {
  id: string;
  name: string;
  geometry: LineString;
  distance_miles: number;
  duration_seconds: number;
  arrival: string;
  checkpoints: Checkpoint[];
  segments: FeatureCollection<LineString, { risk: Risk }>;
  summary: {
    miles_by_risk: Record<Risk, number>;
    average_risk: number | null;
    eligible: boolean;
  };
}
export interface PlanRequest {
  origin: Location;
  destination: Location;
  departure: string;
  load_lbs: number;
  spacing_miles: 10 | 25 | 50;
  mode: Mode;
  scenario?: Scenario;
}
export interface Plan {
  id: string;
  mode: Mode;
  generated_at: string;
  departure: string;
  timezone: string;
  load_lbs: number;
  spacing_miles: number;
  routes: Route[];
  recommended_route_id: string | null;
  recommendation_reason: string;
  warnings: string[];
}
export interface Corridor {
  plan_id: string;
  mode: Mode;
  start_time: string;
  hours: number[];
  resolution_miles: number;
  geojson: FeatureCollection<
    Polygon,
    {
      risks: Risk[];
      wind_mph: (number | null)[];
      rain_in_hr: (number | null)[];
      snow_in_hr: (number | null)[];
    }
  >;
  warnings: string[];
}
export interface Health {
  status: string;
  routing_configured: boolean;
}
