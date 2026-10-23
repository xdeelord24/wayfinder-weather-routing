import { DateTime } from "luxon";
import type { Location, Risk } from "./types";

export const RISKS: Risk[] = [
  "low",
  "moderate",
  "high",
  "severe",
  "no_travel",
  "unknown",
];
export const RISK_LABELS: Record<Risk, string> = {
  low: "Low",
  moderate: "Moderate",
  high: "High",
  severe: "Severe",
  no_travel: "No travel",
  unknown: "Unavailable",
};
export const RISK_COLORS: Record<Risk, string> = {
  low: "#299580",
  moderate: "#dfb444",
  high: "#e78d44",
  severe: "#d75a49",
  no_travel: "#9d3751",
  unknown: "#8795a0",
};
export const CHICAGO: Location = {
  id: "demo-chicago",
  label: "Chicago, IL",
  lat: 41.8781,
  lon: -87.6298,
  timezone: "America/Chicago",
};
export const DETROIT: Location = {
  id: "demo-detroit",
  label: "Detroit, MI",
  lat: 42.3314,
  lon: -83.0458,
  timezone: "America/Detroit",
};
export function duration(seconds: number): string {
  const m = Math.round(seconds / 60);
  return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, "0")}m`;
}
export function miles(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 1 });
}
export function clock(iso: string, zone: string, date = false): string {
  const dt = DateTime.fromISO(iso).setZone(zone);
  return dt.isValid
    ? dt.toFormat(date ? "ccc, LLL d · h:mm a ZZZZ" : "h:mm a ZZZZ")
    : "Time unavailable";
}
export function futureDeparture(
  zone: string,
  now: DateTime = DateTime.now(),
): string {
  return now
    .setZone(zone)
    .plus({ hours: 1 })
    .startOf("minute")
    .toFormat("yyyy-MM-dd'T'HH:mm");
}
export function localLimits(zone: string, now: DateTime = DateTime.now()) {
  return {
    min: now.setZone(zone).startOf("minute").toFormat("yyyy-MM-dd'T'HH:mm"),
    max: now
      .setZone(zone)
      .plus({ hours: 48 })
      .startOf("minute")
      .toFormat("yyyy-MM-dd'T'HH:mm"),
  };
}
export function departureOptions(local: string, zone: string): DateTime[] {
  const dt = DateTime.fromISO(local, { zone });
  if (!dt.isValid || dt.toFormat("yyyy-MM-dd'T'HH:mm") !== local) return [];
  return dt.getPossibleOffsets().sort((a, b) => a.toMillis() - b.toMillis());
}
export function validateDeparture(
  local: string,
  zone: string,
  offsetChoice: number | null,
  now: DateTime = DateTime.now(),
): { iso?: string; error?: string; ambiguous: boolean } {
  const options = departureOptions(local, zone);
  if (!options.length)
    return {
      error:
        "This local time does not exist because of the daylight saving clock change. Choose another time.",
      ambiguous: false,
    };
  if (options.length > 1 && offsetChoice === null)
    return {
      error: "This time occurs twice. Choose which UTC offset to use below.",
      ambiguous: true,
    };
  const choice =
    options.find((item) => item.offset === offsetChoice) ?? options[0];
  if (
    choice.toMillis() < now.minus({ minutes: 1 }).toMillis() ||
    choice.toMillis() > now.plus({ hours: 48 }).toMillis()
  )
    return {
      error: "Choose a departure within the next 48 hours.",
      ambiguous: options.length > 1,
    };
  return { iso: choice.toISO()!, ambiguous: options.length > 1 };
}
export function shortLocation(location: Location): string {
  return location.label.split(",")[0];
}
