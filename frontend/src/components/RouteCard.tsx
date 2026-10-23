import {
  ArrowUpRight,
  Check,
  CircleSlash,
  Clock3,
  ShieldCheck,
} from "lucide-react";
import type { Route } from "../types";
import {
  clock,
  duration,
  miles,
  RISKS,
  RISK_COLORS,
  RISK_LABELS,
} from "../utils";

interface Props {
  route: Route;
  index: number;
  selected: boolean;
  recommended: boolean;
  timezone: string;
  onSelect: () => void;
}
export default function RouteCard({
  route,
  index,
  selected,
  recommended,
  timezone,
  onSelect,
}: Props) {
  return (
    <button
      type="button"
      className={`route-card ${selected ? "selected" : ""} ${recommended ? "recommended" : ""}`}
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`${route.name}, ${recommended ? "recommended, " : ""}${duration(route.duration_seconds)}, ${miles(route.distance_miles)} miles${route.summary.eligible ? "" : ", ineligible for travel"}`}
    >
      {recommended && (
        <div className="recommendation-ribbon">
          <ShieldCheck size={13} /> RECOMMENDED ROUTE <Check size={13} />
        </div>
      )}
      <div className="route-card-body">
        <div className="route-title">
          <span className="route-index">
            {String(index + 1).padStart(2, "0")}
          </span>
          <strong>{route.name}</strong>
          <span className={`selection-radio ${selected ? "checked" : ""}`}>
            {selected && <span />}
          </span>
        </div>
        <div className="route-metrics">
          <span className="duration">{duration(route.duration_seconds)}</span>
          <span className="metric-divider" />
          <span>
            {miles(route.distance_miles)} <small>mi</small>
          </span>
          {!route.summary.eligible && (
            <span className="ineligible-label">
              <CircleSlash size={11} /> Ineligible
            </span>
          )}
        </div>
        <div className="arrival">
          <Clock3 size={12} /> Arrive {clock(route.arrival, timezone)}
        </div>
        <div className="risk-bar" aria-label="Route risk by distance">
          {RISKS.map((risk) => {
            const value = route.summary.miles_by_risk[risk] ?? 0;
            return (
              value > 0 && (
                <span
                  key={risk}
                  style={{ flex: value, background: RISK_COLORS[risk] }}
                  title={`${RISK_LABELS[risk]}: ${miles(value)} mi`}
                />
              )
            );
          })}
        </div>
        <div className="risk-mileage">
          <span>
            <i style={{ background: RISK_COLORS.severe }} />
            {miles(route.summary.miles_by_risk.severe ?? 0)} mi severe
          </span>
          <span>
            <i style={{ background: RISK_COLORS.high }} />
            {miles(route.summary.miles_by_risk.high ?? 0)} mi high
          </span>
          <ArrowUpRight size={14} />
        </div>
        {(route.summary.miles_by_risk.no_travel ?? 0) > 0 && (
          <div className="route-warning">
            {miles(route.summary.miles_by_risk.no_travel)} mi under no travel
            conditions
          </div>
        )}
        {(route.summary.miles_by_risk.unknown ?? 0) > 0 && (
          <div className="route-warning unknown">
            Weather unavailable for {miles(route.summary.miles_by_risk.unknown)}{" "}
            mi
          </div>
        )}
      </div>
    </button>
  );
}
