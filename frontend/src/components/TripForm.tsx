import { useState } from "react";
import {
  ArrowRight,
  ArrowUpDown,
  CalendarDays,
  ChevronDown,
  Clock3,
  Info,
  Route as RouteIcon,
  Weight,
} from "lucide-react";
import { DateTime } from "luxon";
import type { Health, Location, Mode, PlanRequest, Scenario } from "../types";
import {
  CHICAGO,
  DETROIT,
  departureOptions,
  futureDeparture,
  localLimits,
  validateDeparture,
} from "../utils";
import LocationField from "./LocationField";

interface Props {
  mode: Mode;
  scenario: Scenario;
  setScenario: (value: Scenario) => void;
  loading: boolean;
  health: Health | null;
  onSubmit: (request: PlanRequest) => void;
}
export default function TripForm({
  mode,
  scenario,
  setScenario,
  loading,
  health,
  onSubmit,
}: Props) {
  const [origin, setOrigin] = useState<Location | null>(
    mode === "demo" ? CHICAGO : null,
  );
  const [destination, setDestination] = useState<Location | null>(
    mode === "demo" ? DETROIT : null,
  );
  const [departure, setDeparture] = useState(futureDeparture(CHICAGO.timezone));
  const [weight, setWeight] = useState("32000");
  const [spacing, setSpacing] = useState<10 | 25 | 50>(25);
  const [error, setError] = useState("");
  const [offset, setOffset] = useState<number | null>(null);
  const zone = origin?.timezone ?? CHICAGO.timezone;
  const possibleOffsets = departureOptions(departure, zone);
  const limits = localLimits(zone);
  const changeOrigin = (value: Location | null) => {
    setOrigin(value);
    setOffset(null);
    if (value && value.timezone !== zone)
      setDeparture(futureDeparture(value.timezone));
  };
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!origin || !destination) {
      setError(
        "Choose an origin and destination from the location suggestions.",
      );
      return;
    }
    if (origin.lat === destination.lat && origin.lon === destination.lon) {
      setError("Choose a different destination.");
      return;
    }
    const departureResult = validateDeparture(departure, zone, offset);
    if (departureResult.error || !departureResult.iso) {
      setError(departureResult.error ?? "Enter a valid departure.");
      return;
    }
    const load = Number(weight);
    if (!weight.trim() || !Number.isFinite(load) || load < 0 || load > 200000) {
      setError("Enter a load weight between 0 and 200,000 lb.");
      return;
    }
    onSubmit({
      origin,
      destination,
      departure: departureResult.iso,
      load_lbs: load,
      spacing_miles: spacing,
      mode,
      ...(mode === "demo" ? { scenario } : {}),
    });
  };
  return (
    <form className="trip-form" onSubmit={submit}>
      <div className="section-eyebrow">THE ROAD AHEAD</div>
      <h1>Plan a safer journey.</h1>
      <p className="form-intro">Know the weather before it meets you.</p>
      <div className="location-pair">
        <LocationField
          label="Starting point"
          value={origin}
          mode={mode}
          onChange={changeOrigin}
        />
        <button
          type="button"
          className="swap-button"
          aria-label="Swap origin and destination"
          disabled={mode === "demo"}
          title={
            mode === "demo"
              ? "The demo follows Chicago to Detroit."
              : "Swap origin and destination"
          }
          onClick={() => {
            const previous = origin;
            changeOrigin(destination);
            setDestination(previous);
          }}
        >
          <ArrowUpDown size={14} />
        </button>
        <LocationField
          label="Destination"
          value={destination}
          mode={mode}
          onChange={setDestination}
          destination
        />
      </div>
      <label className="field-label" htmlFor="departure">
        <CalendarDays size={13} /> Departure
      </label>
      <div className="standard-input">
        <input
          id="departure"
          type="datetime-local"
          min={limits.min}
          max={limits.max}
          value={departure}
          required
          onChange={(e) => {
            setDeparture(e.target.value);
            setOffset(null);
          }}
        />
      </div>
      <div className="timezone-note">
        <Clock3 size={11} />{" "}
        {origin
          ? `${zone.replaceAll("_", " ")} · next 48 hours`
          : "Select an origin to use its local time"}
      </div>
      {possibleOffsets.length > 1 && (
        <div className="dst-notice">
          <Info size={16} />
          <div>
            This time happens twice during the clock change.
            <select
              aria-label="Daylight saving time offset"
              value={offset ?? ""}
              onChange={(e) => setOffset(Number(e.target.value))}
            >
              <option value="" disabled>
                Choose an offset
              </option>
              {possibleOffsets.map((dt) => (
                <option key={dt.offset} value={dt.offset}>
                  {dt.toFormat("ZZZZ")} (UTC{dt.toFormat("ZZ")})
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
      <div className="form-row">
        <div>
          <label className="field-label" htmlFor="load">
            <Weight size={13} /> Load weight
          </label>
          <div className="standard-input">
            <input
              id="load"
              type="number"
              min="0"
              max="200000"
              step="1"
              value={weight}
              required
              onChange={(e) => setWeight(e.target.value)}
            />
            <span>lb</span>
          </div>
        </div>
        <div>
          <label className="field-label" htmlFor="spacing">
            <RouteIcon size={13} /> Checkpoints
          </label>
          <div className="standard-input select-input">
            <select
              id="spacing"
              value={spacing}
              onChange={(e) =>
                setSpacing(Number(e.target.value) as 10 | 25 | 50)
              }
            >
              <option value={10}>Every 10 mi</option>
              <option value={25}>Every 25 mi</option>
              <option value={50}>Every 50 mi</option>
            </select>
            <ChevronDown size={14} />
          </div>
        </div>
      </div>
      {mode === "demo" && (
        <div className="scenario-field">
          <label className="field-label" htmlFor="scenario">
            Explore a weather scenario
          </label>
          <select
            id="scenario"
            value={scenario}
            onChange={(e) => setScenario(e.target.value as Scenario)}
          >
            <option value="mixed">Mixed conditions</option>
            <option value="clear">Clear skies</option>
            <option value="blocked">No travel conditions</option>
          </select>
        </div>
      )}
      {mode === "live" && health?.routing_configured === false && (
        <div className="notice warning">
          <Info size={17} />
          <span>
            Live routing needs a routing API key on the server. Explore the
            working demo while it is configured.
          </span>
        </div>
      )}
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      <button
        type="submit"
        className="primary-button"
        disabled={
          loading || (mode === "live" && health?.routing_configured === false)
        }
      >
        {loading ? (
          <>
            <span className="spinner" /> Checking the road ahead…
          </>
        ) : (
          <>
            Find safest routes <ArrowRight size={17} />
          </>
        )}
      </button>
      <div className="form-footnote">
        Weather assessed at your arrival time.
      </div>
      <span className="sr-only">
        Current date {DateTime.now().setZone(zone).toISODate()}
      </span>
    </form>
  );
}
