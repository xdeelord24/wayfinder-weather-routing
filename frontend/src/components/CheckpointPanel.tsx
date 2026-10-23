import { Clock3, CloudRain, MapPin, Snowflake, Wind, X } from "lucide-react";
import type { Checkpoint, Route } from "../types";
import { clock, miles, RISK_COLORS, RISK_LABELS } from "../utils";

export default function CheckpointPanel({
  checkpoint,
  route,
  timezone,
  onClose,
}: {
  checkpoint: Checkpoint;
  route: Route;
  timezone: string;
  onClose: () => void;
}) {
  const index = route.checkpoints.findIndex(
    (item) => item.id === checkpoint.id,
  );
  return (
    <aside className="checkpoint-panel" aria-label="Checkpoint weather details">
      <div className="checkpoint-heading">
        <span>
          <MapPin size={14} /> CHECKPOINT {String(index + 1).padStart(2, "0")}
        </span>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close checkpoint details"
        >
          <X size={17} />
        </button>
      </div>
      <div
        className="checkpoint-risk"
        style={{ color: RISK_COLORS[checkpoint.risk] }}
      >
        <i style={{ background: RISK_COLORS[checkpoint.risk] }} />
        {RISK_LABELS[checkpoint.risk]} risk
      </div>
      <p>
        {route.name} · Mile {miles(checkpoint.distance_miles)}
      </p>
      <div className="checkpoint-eta">
        <Clock3 size={14} /> {clock(checkpoint.eta, timezone, true)}
      </div>
      {checkpoint.weather ? (
        <div className="weather-metrics">
          <div>
            <Wind size={18} />
            <strong>{checkpoint.weather.wind_mph.toFixed(1)}</strong>
            <small>mph wind</small>
          </div>
          <div>
            <CloudRain size={18} />
            <strong>{checkpoint.weather.rain_in_hr.toFixed(2)}</strong>
            <small>in/hr rain</small>
          </div>
          <div>
            <Snowflake size={18} />
            <strong>{checkpoint.weather.snow_in_hr.toFixed(2)}</strong>
            <small>in/hr snow</small>
          </div>
        </div>
      ) : (
        <div className="notice warning">
          Forecast unavailable at this checkpoint.
        </div>
      )}
      <ul className="checkpoint-reasons">
        {checkpoint.reasons.map((reason, i) => (
          <li key={i}>{reason}</li>
        ))}
      </ul>
      <div className="checkpoint-footer">
        Represents approximately {miles(checkpoint.exposure_miles)} route miles.
      </div>
    </aside>
  );
}
