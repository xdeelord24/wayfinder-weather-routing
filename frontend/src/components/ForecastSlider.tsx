import { useEffect, useState } from "react";
import {
  CloudSun,
  Eye,
  EyeOff,
  Info,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";
import { DateTime } from "luxon";
import type { Corridor, Mode } from "../types";
import { clock } from "../utils";

interface Props {
  corridor: Corridor | null;
  loading: boolean;
  error: string;
  hour: number;
  setHour: (hour: number) => void;
  timezone: string;
  showWeather: boolean;
  toggleWeather: () => void;
  retry: () => void;
  mode: Mode;
}
export default function ForecastSlider({
  corridor,
  loading,
  error,
  hour,
  setHour,
  timezone,
  showWeather,
  toggleWeather,
  retry,
  mode,
}: Props) {
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    setPlaying(false);
  }, [corridor]);
  useEffect(() => {
    if (!playing || !corridor) return;
    const timer = window.setTimeout(
      () => setHour(hour >= 48 ? 0 : hour + 1),
      700,
    );
    return () => window.clearTimeout(timer);
  }, [playing, hour, corridor, setHour]);
  const selected = corridor
    ? DateTime.fromISO(corridor.start_time).plus({ hours: hour }).toISO()!
    : null;
  return (
    <section className="forecast-panel" aria-label="Trip corridor forecast">
      <div className="forecast-heading">
        <div className="forecast-label">
          <CloudSun size={20} />
          <div>
            <strong>Along the corridor</strong>
            <span>
              {mode === "demo" ? "Simulated weather" : "Weather forecast"} ·
              48-hour outlook
            </span>
          </div>
        </div>
        <button
          type="button"
          className={`weather-toggle ${showWeather ? "active" : ""}`}
          onClick={toggleWeather}
          aria-pressed={showWeather}
          aria-label={
            showWeather ? "Hide weather heatmap" : "Show weather heatmap"
          }
        >
          {showWeather ? <Eye size={14} /> : <EyeOff size={14} />}
          <span>Weather layer</span>
        </button>
      </div>
      {loading ? (
        <div className="forecast-status">
          <span className="spinner" /> Loading 49 forecast frames…
        </div>
      ) : error ? (
        <div className="forecast-status error-text">
          <Info size={16} />
          <span>{error}</span>
          <button onClick={retry} aria-label="Retry corridor forecast">
            <RotateCcw size={15} /> Retry
          </button>
        </div>
      ) : !corridor ? (
        <div className="forecast-status">
          Plan a trip to explore weather along the road.
        </div>
      ) : (
        <>
          <div className="forecast-time">
            <span>{selected && clock(selected, timezone, true)}</span>
            <strong>
              +{hour}h <small>from departure</small>
            </strong>
          </div>
          <div className="slider-row">
            <button
              type="button"
              className="play-button"
              onClick={() => setPlaying((value) => !value)}
              aria-label={
                playing ? "Pause forecast animation" : "Play forecast animation"
              }
            >
              {playing ? (
                <Pause size={16} fill="currentColor" />
              ) : (
                <Play size={16} fill="currentColor" />
              )}
            </button>
            <div className="slider-track">
              <input
                type="range"
                min="0"
                max="48"
                step="1"
                value={hour}
                onChange={(e) => {
                  setPlaying(false);
                  setHour(Number(e.target.value));
                }}
                aria-label="Forecast hours after departure"
                aria-valuetext={`${hour} hours after departure`}
                style={
                  {
                    "--progress": `${(hour / 48) * 100}%`,
                  } as React.CSSProperties
                }
              />
              <div className="slider-ticks">
                <span>Departure</span>
                <span>+12h</span>
                <span>+24h</span>
                <span>+36h</span>
                <span>+48h</span>
              </div>
            </div>
          </div>
          <div className="forecast-footnote">
            <Info size={11} /> Map snapshot only. Route ranking uses weather at
            each checkpoint’s ETA.
          </div>
        </>
      )}
    </section>
  );
}
