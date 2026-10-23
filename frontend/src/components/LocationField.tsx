import { useEffect, useId, useState } from "react";
import { MapPin, Search, X } from "lucide-react";
import { api } from "../api";
import type { Location, Mode } from "../types";

interface Props {
  label: string;
  value: Location | null;
  mode: Mode;
  onChange: (value: Location | null) => void;
  destination?: boolean;
}
export default function LocationField({
  label,
  value,
  mode,
  onChange,
  destination,
}: Props) {
  const id = useId();
  const [query, setQuery] = useState(value?.label ?? "");
  const [focused, setFocused] = useState(false);
  const [options, setOptions] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(-1);
  useEffect(() => {
    if (value) setQuery(value.label);
  }, [value]);
  useEffect(() => {
    setOptions([]);
    setActive(-1);
    setError("");
    if (!focused || query.trim().length < 2 || query === value?.label) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setLoading(true);
      api
        .locations(query.trim(), mode, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) setOptions(data.locations);
        })
        .catch((e: Error) => {
          if (!controller.signal.aborted) setError(e.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 300);
    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [query, mode, focused, value?.label]);
  const choose = (location: Location) => {
    onChange(location);
    setQuery(location.label);
    setFocused(false);
    setOptions([]);
  };
  return (
    <div className="location-field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <div className={`location-input ${focused ? "focused" : ""}`}>
        {destination ? (
          <MapPin size={16} className="destination-icon" />
        ) : (
          <span className="origin-dot" />
        )}
        <input
          id={id}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={focused && options.length > 0}
          aria-controls={`${id}-options`}
          aria-activedescendant={
            active >= 0 ? `${id}-option-${active}` : undefined
          }
          value={query}
          placeholder="Search a city or address"
          autoComplete="off"
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(e) => {
            setQuery(e.target.value);
            if (value) onChange(null);
            setFocused(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActive((n) => Math.min(n + 1, options.length - 1));
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((n) => Math.max(n - 1, 0));
            }
            if (e.key === "Enter" && active >= 0 && options[active]) {
              e.preventDefault();
              choose(options[active]);
            }
            if (e.key === "Escape") setFocused(false);
          }}
        />
        {query && (
          <button
            type="button"
            className="icon-button clear-location"
            aria-label={`Clear ${label.toLowerCase()}`}
            onClick={() => {
              onChange(null);
              setQuery("");
              setFocused(true);
            }}
          >
            <X size={13} />
          </button>
        )}
      </div>
      {focused && query.length >= 2 && query !== value?.label && (
        <div
          className="location-options"
          id={`${id}-options`}
          role="listbox"
          aria-label={`${label} suggestions`}
        >
          {loading ? (
            <div className="search-state">
              <span className="spinner" /> Finding places…
            </div>
          ) : error ? (
            <div className="search-state error-text">{error}</div>
          ) : options.length ? (
            options.map((location, index) => (
              <button
                type="button"
                role="option"
                aria-selected={active === index}
                id={`${id}-option-${index}`}
                key={location.id}
                className={active === index ? "active" : ""}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(location)}
              >
                <Search size={15} />
                <span>
                  {location.label}
                  <small>{location.timezone.replaceAll("_", " ")}</small>
                </span>
              </button>
            ))
          ) : (
            <div className="search-state">
              {mode === "demo"
                ? "Demo locations: Chicago and Detroit."
                : "No matching locations."}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
