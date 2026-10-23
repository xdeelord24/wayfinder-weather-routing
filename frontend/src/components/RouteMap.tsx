import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import mapWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import type { ExpressionSpecification, GeoJSONSource } from "maplibre-gl";
import type { FeatureCollection, LineString, Point } from "geojson";
import { Expand, Info, Layers, Minus, Plus } from "lucide-react";
import type { Corridor, Plan, Risk } from "../types";
import { RISK_COLORS, RISK_LABELS, RISKS } from "../utils";

// Bundle the worker and its shared-module imports in both Vite dev and production.
maplibregl.setWorkerUrl(mapWorkerUrl);

interface Props {
  plan: Plan | null;
  corridor: Corridor | null;
  selectedRouteId: string | null;
  hour: number;
  showWeather: boolean;
  onSelectRoute: (id: string) => void;
  onSelectCheckpoint: (routeId: string, checkpointId: string) => void;
}
const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
function colorExpression(
  input: ExpressionSpecification,
): ExpressionSpecification {
  return [
    "match",
    input,
    ...RISKS.flatMap((risk) => [risk, RISK_COLORS[risk]]),
    RISK_COLORS.unknown,
  ] as ExpressionSpecification;
}

export default function RouteMap({
  plan,
  corridor,
  selectedRouteId,
  hour,
  showWeather,
  onSelectRoute,
  onSelectCheckpoint,
}: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const callbacks = useRef({ onSelectRoute, onSelectCheckpoint });
  const planRef = useRef(plan);
  const selectedRouteRef = useRef(selectedRouteId);
  callbacks.current = { onSelectRoute, onSelectCheckpoint };
  planRef.current = plan;
  selectedRouteRef.current = selectedRouteId;
  const [ready, setReady] = useState(false);
  const [mapError, setMapError] = useState("");
  const [legendOpen, setLegendOpen] = useState(false);
  const fit = (duration = 900) => {
    const map = mapRef.current;
    const activePlan = planRef.current;
    if (!map || !activePlan?.routes.length) return;
    const bounds = new maplibregl.LngLatBounds();
    activePlan.routes.forEach((route) =>
      route.geometry.coordinates.forEach((point) =>
        bounds.extend([point[0], point[1]]),
      ),
    );
    const narrow = map.getContainer().clientWidth < 600;
    const height = map.getContainer().clientHeight;
    if (!bounds.isEmpty())
      map.fitBounds(bounds, {
        padding: {
          top: Math.min(140, height * 0.22),
          bottom: Math.min(narrow ? 230 : 190, height * 0.34),
          left: narrow ? 32 : 72,
          right: narrow ? 32 : 72,
        },
        maxZoom: 9,
        duration,
      });
  };
  useEffect(() => {
    if (!container.current) return;
    let map: maplibregl.Map;
    try {
      map = new maplibregl.Map({
        container: container.current,
        center: [-85.4, 42.1],
        zoom: 6.4,
        minZoom: 2,
        maxZoom: 17,
        attributionControl: false,
        style: {
          version: 8,
          sources: {
            basemap: {
              type: "raster",
              tiles: [
                import.meta.env.VITE_MAP_TILE_URL ||
                  "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
              ],
              tileSize: 256,
              attribution:
                import.meta.env.VITE_MAP_ATTRIBUTION ||
                '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
            },
          },
          layers: [
            {
              id: "basemap",
              type: "raster",
              source: "basemap",
              paint: {
                "raster-saturation": -0.7,
                "raster-contrast": -0.08,
                "raster-brightness-min": 0.12,
                "raster-brightness-max": 0.98,
              },
            },
          ],
        },
      });
    } catch {
      setMapError(
        "The map needs WebGL. Your route comparison and checkpoint details are still available.",
      );
      return;
    }
    mapRef.current = map;
    map.addControl(
      new maplibregl.AttributionControl({ compact: false }),
      "bottom-left",
    );
    map.on("error", (event) => {
      if (event.error.message.includes("WebGL"))
        setMapError(
          "The map could not initialize WebGL. Try another browser or enable hardware acceleration.",
        );
      if (/worker/i.test(event.error.message))
        setMapError(
          "Map data could not be drawn. Refresh to reload the map; route comparison and checkpoint details remain available.",
        );
    });
    map.on("load", () => {
      map.addSource("corridor", { type: "geojson", data: empty });
      map.addLayer({
        id: "corridor-fill",
        type: "fill",
        source: "corridor",
        paint: {
          "fill-color": colorExpression(["at", 0, ["get", "risks"]]),
          "fill-opacity": 0.2,
        },
      });
      map.addLayer({
        id: "corridor-stroke",
        type: "line",
        source: "corridor",
        paint: {
          "line-color": colorExpression(["at", 0, ["get", "risks"]]),
          "line-opacity": 0.12,
          "line-width": 0.5,
        },
      });
      map.addSource("routes", { type: "geojson", data: empty });
      map.addLayer({
        id: "route-outline",
        type: "line",
        source: "routes",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": "#ffffff",
          "line-width": 8,
          "line-opacity": 0.9,
        },
      });
      map.addLayer({
        id: "route-lines",
        type: "line",
        source: "routes",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#8797a0", "line-width": 4 },
      });
      map.addSource("segments", { type: "geojson", data: empty });
      map.addLayer({
        id: "risk-segments",
        type: "line",
        source: "segments",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": colorExpression(["get", "risk"]),
          "line-width": 4,
          "line-opacity": 0.75,
        },
      });
      map.addLayer({
        id: "selected-route-outline",
        type: "line",
        source: "routes",
        filter: ["==", ["get", "route_id"], ""],
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#153a45", "line-width": 9 },
      });
      map.addLayer({
        id: "selected-risk-segments",
        type: "line",
        source: "segments",
        filter: ["==", ["get", "route_id"], ""],
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": colorExpression(["get", "risk"]),
          "line-width": 5.5,
        },
      });
      map.addLayer({
        id: "route-hit-area",
        type: "line",
        source: "routes",
        paint: { "line-width": 20, "line-opacity": 0 },
      });
      map.addSource("checkpoints", { type: "geojson", data: empty });
      map.addLayer({
        id: "all-checkpoint-circles",
        type: "circle",
        source: "checkpoints",
        paint: {
          "circle-radius": 3,
          "circle-color": colorExpression(["get", "risk"]),
          "circle-stroke-color": "#fff",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.8,
        },
      });
      map.addLayer({
        id: "checkpoint-circles",
        type: "circle",
        source: "checkpoints",
        filter: ["==", ["get", "route_id"], ""],
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            4,
            3,
            8,
            5,
            12,
            7,
          ],
          "circle-color": colorExpression(["get", "risk"]),
          "circle-stroke-color": "#fff",
          "circle-stroke-width": 2,
        },
      });
      map.addLayer({
        id: "checkpoint-hit-area",
        type: "circle",
        source: "checkpoints",
        paint: { "circle-radius": 14, "circle-opacity": 0 },
      });
      map.addSource("endpoints", { type: "geojson", data: empty });
      map.addLayer({
        id: "endpoint-circles",
        type: "circle",
        source: "endpoints",
        paint: {
          "circle-radius": 8,
          "circle-color": "#173a45",
          "circle-stroke-color": "#fff",
          "circle-stroke-width": 3,
        },
      });
      map.addLayer({
        id: "endpoint-inner",
        type: "circle",
        source: "endpoints",
        paint: { "circle-radius": 3, "circle-color": "#fff" },
      });
      map.on("click", (event) => {
        const nearbyCheckpoints = map.queryRenderedFeatures(event.point, {
          layers: ["checkpoint-hit-area"],
        });
        const checkpoint =
          nearbyCheckpoints.find(
            (feature) =>
              feature.properties?.route_id === selectedRouteRef.current,
          ) ?? nearbyCheckpoints[0];
        if (checkpoint?.properties) {
          callbacks.current.onSelectCheckpoint(
            checkpoint.properties.route_id,
            checkpoint.properties.checkpoint_id,
          );
          return;
        }
        const route = map.queryRenderedFeatures(event.point, {
          layers: ["route-hit-area"],
        })[0];
        if (route?.properties?.route_id)
          callbacks.current.onSelectRoute(route.properties.route_id);
      });
      map.on("mousemove", (event) => {
        const features = map.queryRenderedFeatures(event.point, {
          layers: ["checkpoint-hit-area", "route-hit-area"],
        });
        map.getCanvas().style.cursor = features.length ? "pointer" : "";
      });
      setReady(true);
    });
    let resizeTimer: number | undefined;
    let previousSize = "";
    const resize = new ResizeObserver((entries) => {
      const bounds = entries[0]?.contentRect;
      const size = bounds
        ? `${Math.round(bounds.width)}:${Math.round(bounds.height)}`
        : "";
      if (size === previousSize) return;
      previousSize = size;
      map.resize();
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(() => fit(0), 120);
    });
    resize.observe(container.current);
    return () => {
      resize.disconnect();
      window.clearTimeout(resizeTimer);
      map.remove();
      mapRef.current = null;
      setReady(false);
    };
  }, []);
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const routes: FeatureCollection<LineString> = {
      type: "FeatureCollection",
      features:
        plan?.routes.map((route) => ({
          type: "Feature",
          geometry: route.geometry,
          properties: { route_id: route.id },
        })) ?? [],
    };
    const segments: FeatureCollection<LineString> = {
      type: "FeatureCollection",
      features:
        plan?.routes.flatMap((route) =>
          route.segments.features.map((feature) => ({
            ...feature,
            properties: { ...feature.properties, route_id: route.id },
          })),
        ) ?? [],
    };
    const checkpoints: FeatureCollection<Point> = {
      type: "FeatureCollection",
      features:
        plan?.routes.flatMap((route) =>
          route.checkpoints.map((checkpoint) => ({
            type: "Feature" as const,
            geometry: {
              type: "Point" as const,
              coordinates: [checkpoint.lon, checkpoint.lat],
            },
            properties: {
              route_id: route.id,
              checkpoint_id: checkpoint.id,
              risk: checkpoint.risk,
            },
          })),
        ) ?? [],
    };
    const coordinates = plan?.routes[0]?.geometry.coordinates ?? [];
    const endpoints: FeatureCollection<Point> = {
      type: "FeatureCollection",
      features: coordinates.length
        ? [coordinates[0], coordinates[coordinates.length - 1]].map(
            (point) => ({
              type: "Feature",
              geometry: { type: "Point", coordinates: point },
              properties: {},
            }),
          )
        : [],
    };
    (map.getSource("routes") as GeoJSONSource).setData(routes);
    (map.getSource("segments") as GeoJSONSource).setData(segments);
    (map.getSource("checkpoints") as GeoJSONSource).setData(checkpoints);
    (map.getSource("endpoints") as GeoJSONSource).setData(endpoints);
    fit();
  }, [plan, ready]);
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    for (const layer of [
      "selected-route-outline",
      "selected-risk-segments",
      "checkpoint-circles",
    ])
      map.setFilter(layer, ["==", ["get", "route_id"], selectedRouteId ?? ""]);
  }, [selectedRouteId, ready]);
  useEffect(() => {
    const map = mapRef.current;
    if (ready && map)
      (map.getSource("corridor") as GeoJSONSource).setData(
        corridor?.geojson ?? empty,
      );
  }, [corridor, ready]);
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    map.setPaintProperty(
      "corridor-fill",
      "fill-color",
      colorExpression(["at", hour, ["get", "risks"]]),
    );
    map.setPaintProperty(
      "corridor-stroke",
      "line-color",
      colorExpression(["at", hour, ["get", "risks"]]),
    );
    for (const layer of ["corridor-fill", "corridor-stroke"])
      map.setLayoutProperty(
        layer,
        "visibility",
        showWeather ? "visible" : "none",
      );
  }, [hour, showWeather, ready]);
  return (
    <>
      <div
        className="map-canvas"
        ref={container}
        aria-label="Interactive map showing truck routes, weather risk and checkpoints"
      />
      {mapError && (
        <div className="map-error" role="alert">
          <Info size={18} />
          {mapError}
        </div>
      )}
      <div className="map-controls">
        <button onClick={() => fit()} aria-label="Fit all routes">
          <Expand size={18} />
        </button>
        <span />
        <button onClick={() => mapRef.current?.zoomIn()} aria-label="Zoom in">
          <Plus size={20} />
        </button>
        <button onClick={() => mapRef.current?.zoomOut()} aria-label="Zoom out">
          <Minus size={20} />
        </button>
      </div>
      <div className={`map-legend ${legendOpen ? "expanded" : ""}`}>
        <button
          className="legend-toggle"
          onClick={() => setLegendOpen((value) => !value)}
          aria-expanded={legendOpen}
        >
          <Layers size={14} /> Risk legend
        </button>
        <div className="legend-items">
          {RISKS.map((risk: Risk) => (
            <span key={risk}>
              <i style={{ background: RISK_COLORS[risk] }} />
              {RISK_LABELS[risk]}
            </span>
          ))}
        </div>
      </div>
    </>
  );
}
