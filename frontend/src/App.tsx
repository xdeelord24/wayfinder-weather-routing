import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  CloudSun,
  Info,
  MapPin,
  Navigation,
  ShieldCheck,
  Truck,
  X,
} from "lucide-react";
import { DateTime } from "luxon";
import { api } from "./api";
import type {
  Corridor,
  Health,
  Mode,
  Plan,
  PlanRequest,
  Scenario,
} from "./types";
import {
  CHICAGO,
  DETROIT,
  clock,
  duration,
  miles,
  RISK_COLORS,
  RISK_LABELS,
  shortLocation,
} from "./utils";
import TripForm from "./components/TripForm";
import RouteCard from "./components/RouteCard";
import ForecastSlider from "./components/ForecastSlider";
import CheckpointPanel from "./components/CheckpointPanel";

const RouteMap = lazy(() => import("./components/RouteMap"));

export default function App() {
  const [mode, setMode] = useState<Mode>("demo");
  const [scenario, setScenario] = useState<Scenario>("mixed");
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [corridor, setCorridor] = useState<Corridor | null>(null);
  const [activeTrip, setActiveTrip] = useState<PlanRequest | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [corridorLoading, setCorridorLoading] = useState(false);
  const [error, setError] = useState("");
  const [corridorError, setCorridorError] = useState("");
  const [hour, setHour] = useState(0);
  const [showWeather, setShowWeather] = useState(true);
  const [showMethod, setShowMethod] = useState(false);
  const methodDialog = useRef<HTMLElement | null>(null);
  const sequence = useRef(0);
  const pending = useRef<AbortController | null>(null);
  const corridorPending = useRef<AbortController | null>(null);
  const fetchCorridor = useCallback(async (planId: string, current: number) => {
    corridorPending.current?.abort();
    const controller = new AbortController();
    corridorPending.current = controller;
    setCorridorLoading(true);
    setCorridorError("");
    try {
      const result = await api.corridor(planId, controller.signal);
      if (
        sequence.current === current &&
        !controller.signal.aborted &&
        result.plan_id === planId
      )
        setCorridor(result);
    } catch (e) {
      if (!controller.signal.aborted && current === sequence.current)
        setCorridorError(
          e instanceof Error
            ? e.message
            : "The corridor forecast could not be loaded.",
        );
    } finally {
      if (!controller.signal.aborted && current === sequence.current)
        setCorridorLoading(false);
    }
  }, []);
  const findRoutes = useCallback(
    async (input: PlanRequest) => {
      pending.current?.abort();
      corridorPending.current?.abort();
      const controller = new AbortController();
      pending.current = controller;
      const current = ++sequence.current;
      setLoading(true);
      setError("");
      setCorridorError("");
      setPlan(null);
      setCorridor(null);
      setSelectedCheckpoint(null);
      setSelectedRouteId(null);
      setHour(0);
      setCorridorLoading(false);
      try {
        const result = await api.plan(input, controller.signal);
        if (controller.signal.aborted || current !== sequence.current) return;
        setPlan(result);
        setActiveTrip(input);
        setSelectedRouteId(
          result.recommended_route_id ?? result.routes[0]?.id ?? null,
        );
        void fetchCorridor(result.id, current);
      } catch (e) {
        if (!controller.signal.aborted && current === sequence.current)
          setError(
            e instanceof Error
              ? e.message
              : "Routes could not be calculated. Please try again.",
          );
      } finally {
        if (!controller.signal.aborted && current === sequence.current)
          setLoading(false);
      }
    },
    [fetchCorridor],
  );
  useEffect(() => {
    const controller = new AbortController();
    api
      .health(controller.signal)
      .then((result) => {
        setHealth(result);
        setHealthError(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) setHealthError(true);
      });
    void findRoutes({
      origin: CHICAGO,
      destination: DETROIT,
      departure: DateTime.now()
        .setZone(CHICAGO.timezone)
        .plus({ hours: 1 })
        .startOf("minute")
        .toISO()!,
      load_lbs: 32000,
      spacing_miles: 25,
      mode: "demo",
      scenario: "mixed",
    });
    return () => {
      controller.abort();
      pending.current?.abort();
      corridorPending.current?.abort();
      sequence.current += 1;
    };
  }, [findRoutes]);
  useEffect(() => {
    if (!showMethod) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    const controls =
      methodDialog.current?.querySelectorAll<HTMLButtonElement>("button");
    controls?.[0]?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setShowMethod(false);
      if (event.key !== "Tab" || !controls?.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previousFocus?.focus();
    };
  }, [showMethod]);
  const switchMode = (next: Mode) => {
    if (next === mode) return;
    pending.current?.abort();
    corridorPending.current?.abort();
    sequence.current += 1;
    setMode(next);
    setPlan(null);
    setCorridor(null);
    setActiveTrip(null);
    setSelectedRouteId(null);
    setSelectedCheckpoint(null);
    setLoading(false);
    setCorridorLoading(false);
    setError("");
    setCorridorError("");
    setHour(0);
  };
  const selectRoute = (id: string) => {
    setSelectedRouteId(id);
    setSelectedCheckpoint(null);
  };
  const selectedRoute = plan?.routes.find(
    (route) => route.id === selectedRouteId,
  );
  const checkpoint = selectedRoute?.checkpoints.find(
    (point) => point.id === selectedCheckpoint,
  );
  const zone = plan?.timezone ?? CHICAGO.timezone;
  const destinationZone = activeTrip?.destination.timezone ?? zone;
  const displayedRoutes = [...(plan?.routes ?? [])].sort(
    (a, b) =>
      Number(b.id === plan?.recommended_route_id) -
      Number(a.id === plan?.recommended_route_id),
  );
  const warnings = [
    ...new Set([...(plan?.warnings ?? []), ...(corridor?.warnings ?? [])]),
  ];

  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand" href="/" aria-label="Wayfinder home">
          <span className="brand-icon">
            <Navigation size={22} fill="currentColor" />
          </span>
          <span>
            wayfinder<span className="brand-period">.</span>
          </span>
        </a>
        <div className="header-divider" />
        <span className="product-label">WEATHER-AWARE ROUTING</span>
        <nav className="header-nav" aria-label="Application navigation">
          <span className="nav-active">
            <MapPin size={15} /> Trip planner
          </span>
          <button onClick={() => setShowMethod(true)}>
            <CircleHelp size={15} /> How it works
          </button>
        </nav>
        <div className="header-status">
          <span className={healthError ? "status-dot offline" : "status-dot"} />
          {healthError
            ? "Service unavailable"
            : mode === "demo"
              ? "Demo · simulated weather"
              : "Live weather"}
        </div>
      </header>
      <main className="workspace">
        <aside
          className="sidebar"
          aria-label="Trip planning and route comparison"
        >
          <div className="mode-bar">
            <div className="mode-switch" aria-label="Data source">
              <button
                className={mode === "demo" ? "active" : ""}
                onClick={() => switchMode("demo")}
                aria-pressed={mode === "demo"}
              >
                Explore demo
              </button>
              <button
                className={mode === "live" ? "active" : ""}
                onClick={() => switchMode("live")}
                aria-pressed={mode === "live"}
              >
                Live planning
              </button>
            </div>
            <span
              className="mode-info"
              title={
                mode === "demo"
                  ? "Saved driving routes with deterministic, simulated weather."
                  : "Routes and forecasts come from live providers."
              }
            >
              <Info size={15} />
            </span>
          </div>
          <TripForm
            key={mode}
            mode={mode}
            scenario={scenario}
            setScenario={setScenario}
            loading={loading}
            health={health}
            onSubmit={(input) => void findRoutes(input)}
          />
          <section
            className="route-results"
            aria-label="Route results"
            aria-live="polite"
            aria-busy={loading}
          >
            <div className="results-heading">
              <h2>Your route options</h2>
              <span>
                {plan ? `${plan.routes.length} ROUTES` : "COMPARE & CHOOSE"}
              </span>
            </div>
            {error && (
              <div className="notice error" role="alert">
                <Info size={18} />
                <div>
                  <strong>We couldn’t plan this trip</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}
            {loading && (
              <div className="route-skeletons">
                {[0, 1, 2].map((i) => (
                  <div className="route-skeleton" key={i}>
                    <span />
                    <span />
                    <span />
                  </div>
                ))}
                <p>Comparing routes and arrival-time forecasts…</p>
              </div>
            )}
            {plan && (
              <>
                <div
                  className={`recommendation-note ${plan.recommended_route_id ? "" : "blocked"}`}
                >
                  {plan.recommended_route_id ? (
                    <ShieldCheck size={18} />
                  ) : (
                    <Info size={18} />
                  )}
                  <span>{plan.recommendation_reason}</span>
                </div>
                <div className="route-list">
                  {displayedRoutes.map((route, index) => (
                    <RouteCard
                      key={route.id}
                      route={route}
                      index={index}
                      selected={route.id === selectedRouteId}
                      recommended={route.id === plan.recommended_route_id}
                      timezone={destinationZone}
                      onSelect={() => selectRoute(route.id)}
                    />
                  ))}
                </div>
                {selectedRoute && (
                  <details className="checkpoint-list">
                    <summary>
                      <MapPin size={14} /> Inspect{" "}
                      {selectedRoute.checkpoints.length} checkpoints{" "}
                      <ChevronRight size={14} />
                    </summary>
                    <div>
                      {selectedRoute.checkpoints.map((point, index) => (
                        <button
                          key={point.id}
                          onClick={() => setSelectedCheckpoint(point.id)}
                          className={
                            point.id === selectedCheckpoint ? "active" : ""
                          }
                        >
                          <span className="checkpoint-number">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <span>
                            Mile {miles(point.distance_miles)}
                            <small>{clock(point.eta, zone)}</small>
                          </span>
                          <span
                            className="checkpoint-list-risk"
                            style={{ color: RISK_COLORS[point.risk] }}
                          >
                            {RISK_LABELS[point.risk]}
                          </span>
                        </button>
                      ))}
                    </div>
                  </details>
                )}
                <p className="ranking-note">
                  Ranked by severe miles, high miles, average risk, then travel
                  time. No travel and incomplete forecasts are ineligible.
                </p>
              </>
            )}
            {!plan && !loading && !error && (
              <div className="results-empty">
                <Truck size={30} />
                <strong>A better route starts here.</strong>
                <p>
                  Enter your trip above to compare weather and travel time
                  across three route options.
                </p>
              </div>
            )}
            {warnings.length > 0 && (
              <details className="data-warnings">
                <summary>
                  <Info size={13} /> Data notes ({warnings.length})
                </summary>
                <ul>
                  {warnings.map((warning, i) => (
                    <li key={i}>{warning}</li>
                  ))}
                </ul>
              </details>
            )}
          </section>
          <footer className="sidebar-footer">
            <span className="tiny-logo">
              <Navigation size={13} fill="currentColor" />
            </span>{" "}
            A clearer view of the road ahead.
          </footer>
        </aside>
        <section
          className="map-section"
          aria-label="Route map and weather forecast"
        >
          <Suspense
            fallback={
              <div className="map-loading">
                <span className="spinner" /> Loading the map…
              </div>
            }
          >
            <RouteMap
              plan={plan}
              corridor={corridor}
              selectedRouteId={selectedRouteId}
              hour={hour}
              showWeather={showWeather}
              onSelectRoute={selectRoute}
              onSelectCheckpoint={(routeId, checkpointId) => {
                setSelectedRouteId(routeId);
                setSelectedCheckpoint(checkpointId);
              }}
            />
          </Suspense>
          <div className="map-topbar">
            <div className="trip-overview">
              <span className="trip-overview-icon">
                <Truck size={20} />
              </span>
              <div>
                <div className="trip-overview-title">
                  {activeTrip && plan ? (
                    <>
                      {shortLocation(activeTrip.origin)}{" "}
                      <ArrowRight size={15} />{" "}
                      {shortLocation(activeTrip.destination)}
                    </>
                  ) : (
                    "Your journey, in perspective"
                  )}
                </div>
                <div className="trip-overview-subtitle">
                  {selectedRoute ? (
                    <>
                      {duration(selectedRoute.duration_seconds)}
                      <i />
                      {miles(selectedRoute.distance_miles)} miles
                      <i />
                      {selectedRoute.checkpoints.length} weather checks
                    </>
                  ) : (
                    "Route intelligence for the road ahead"
                  )}
                </div>
              </div>
            </div>
            {mode === "demo" && (
              <span className="demo-badge">
                <span /> DEMO · SIMULATED WEATHER
              </span>
            )}
          </div>
          {plan && selectedRoute && (
            <div className="map-route-label">
              <span className="route-label-dot" />
              <strong>{selectedRoute.name}</strong>
              <span>
                {selectedRoute.id === plan.recommended_route_id ? (
                  <>
                    <ShieldCheck size={12} /> Recommended
                  </>
                ) : !selectedRoute.summary.eligible ? (
                  "Ineligible for travel"
                ) : (
                  "Selected route"
                )}
              </span>
            </div>
          )}
          {loading && (
            <div className="map-loading">
              <span className="spinner" />
              <span>Finding your way…</span>
            </div>
          )}
          {!plan && !loading && (
            <div className="map-welcome">
              <span>
                <CloudSun size={27} />
              </span>
              <h2>Weather is part of the journey.</h2>
              <p>
                {mode === "demo"
                  ? "Explore a trip to see conditions along every mile."
                  : health?.routing_configured === false
                    ? "Live routing will be available once the server routing key is configured. The demo is ready to explore."
                    : "Plan a trip to reveal routes and their weather."}
              </p>
            </div>
          )}
          {checkpoint && selectedRoute && (
            <CheckpointPanel
              checkpoint={checkpoint}
              route={selectedRoute}
              timezone={zone}
              onClose={() => setSelectedCheckpoint(null)}
            />
          )}
          <ForecastSlider
            corridor={corridor}
            loading={corridorLoading}
            error={corridorError}
            hour={hour}
            setHour={setHour}
            timezone={zone}
            showWeather={showWeather}
            toggleWeather={() => setShowWeather((value) => !value)}
            retry={() => {
              if (plan) void fetchCorridor(plan.id, sequence.current);
            }}
            mode={mode}
          />
          <div className="map-bottom-note">
            Weather informs decisions. Road restrictions and official alerts
            still apply.
          </div>
        </section>
      </main>
      {showMethod && (
        <div className="modal-backdrop" onClick={() => setShowMethod(false)}>
          <section
            ref={methodDialog}
            className="method-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="method-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="modal-close icon-button"
              onClick={() => setShowMethod(false)}
              aria-label="Close how it works"
            >
              <X size={20} />
            </button>
            <span className="method-icon">
              <ShieldCheck size={27} />
            </span>
            <div className="section-eyebrow">BUILT FOR THE ROAD</div>
            <h2 id="method-title">A clearer route to safer travel.</h2>
            <p>
              Wayfinder samples weather along three routes at your estimated
              arrival time, then applies the assessment’s wind, rain, snow and
              load-weight rules.
            </p>
            <ol>
              <li>
                <Check size={17} />
                <span>
                  <strong>Check every stretch</strong>Choose checkpoints every
                  10, 25 or 50 miles. Between-checkpoint exposure is an
                  estimate.
                </span>
              </li>
              <li>
                <Check size={17} />
                <span>
                  <strong>Put weather risk first</strong>Eligible routes rank by
                  fewest severe miles, then high miles, average risk and travel
                  time. No travel conditions or missing forecasts make a route
                  ineligible.
                </span>
              </li>
              <li>
                <Check size={17} />
                <span>
                  <strong>Look ahead across the corridor</strong>The forecast
                  slider shows a snapshot at departure +0 to +48 hours. It does
                  not change arrival-time route scoring.
                </span>
              </li>
            </ol>
            <div className="notice warning">
              <Info size={17} />
              <span>
                Demo weather is simulated over saved driving routes. Live
                routing uses a truck profile; vehicle dimensions, gross weight
                and hazardous-material restrictions are not configured.
              </span>
            </div>
            <button
              className="primary-button"
              onClick={() => setShowMethod(false)}
            >
              Back to the journey <ArrowRight size={17} />
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
