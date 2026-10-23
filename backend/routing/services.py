from datetime import datetime, timedelta, timezone
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache

from . import demo, providers
from .domain import assess_weather, corridor_grid, finalize_route, iso, recommend, sample_route
from .errors import ServiceError


def create_plan(data):
    departure = data["departure"]
    mode, load = data["mode"], data["load_lbs"]
    scenario = data.get("scenario", "mixed")
    if mode == "demo":
        origin, destination = demo.selected_locations(data["origin"], data["destination"])
        raw_routes = demo.routes()
        warnings = ["Demo uses a saved OSRM/OpenStreetMap driving-road snapshot with sample travel times and synthetic weather. No live provider data or truck restrictions are verified."]
    else:
        origin = providers.selected_live_location(data["origin"])
        destination = providers.selected_live_location(data["destination"])
        raw_routes, warnings = providers.calculate_routes(origin, destination, departure)
    # Re-resolve even demo timezones so the request's timezone is never trusted.
    origin["timezone"] = providers.timezone_at(origin["lat"], origin["lon"])
    checkpoints_by_route = [sample_route(route, data["spacing_miles"], departure, f"route-{index + 1}") for index, route in enumerate(raw_routes)]
    if mode == "live":
        all_checkpoints = [checkpoint for group in checkpoints_by_route for checkpoint in group]
        latest = max(datetime.fromisoformat(checkpoint["eta"].replace("Z", "+00:00")) for checkpoint in all_checkpoints)
        series, weather_warnings = providers.fetch_weather([(point["lat"], point["lon"]) for point in all_checkpoints], departure, latest)
        warnings.extend(weather_warnings)
    result_routes = []
    for index, (route, checkpoints) in enumerate(zip(raw_routes, checkpoints_by_route)):
        for checkpoint in checkpoints:
            eta = datetime.fromisoformat(checkpoint["eta"].replace("Z", "+00:00"))
            if mode == "demo":
                weather = demo.weather(checkpoint["lat"], checkpoint["lon"], eta, departure, scenario)
            else:
                source = series.get(providers.coordinate_key(checkpoint["lat"], checkpoint["lon"]))
                weather = source.at(eta) if source else None
            checkpoint["weather"] = weather
            checkpoint["risk"], checkpoint["reasons"] = assess_weather(weather, load)
        result_routes.append(finalize_route(route, f"route-{index + 1}", checkpoints, departure))
    if any(route["summary"]["miles_by_risk"]["unknown"] > 0 for route in result_routes):
        warnings.append("Some checkpoint arrival times have no complete forecast coverage. A route with any unknown exposure cannot be recommended.")
    recommended, reason = recommend(result_routes)
    plan = {
        "id": str(uuid4()), "mode": mode, "generated_at": iso(datetime.now(timezone.utc)),
        "departure": iso(departure), "timezone": origin["timezone"], "load_lbs": load,
        "spacing_miles": data["spacing_miles"], "routes": result_routes,
        "recommended_route_id": recommended, "recommendation_reason": reason,
        "warnings": list(dict.fromkeys(warnings)),
    }
    cache.set("plan:" + plan["id"], {"response": plan, "routes": raw_routes, "scenario": scenario}, settings.PLAN_CACHE_SECONDS)
    return plan


def create_corridor(plan_id):
    stored = cache.get("plan:" + plan_id)
    if stored is None:
        raise ServiceError("plan_expired", "This plan has expired or the server restarted. Calculate the route again to reload its corridor forecast.", 410)
    cached = cache.get("corridor:" + plan_id)
    if cached is not None:
        return cached
    plan = stored["response"]
    departure = datetime.fromisoformat(plan["departure"].replace("Z", "+00:00"))
    hours = list(range(49))
    resolution, cells = corridor_grid(stored["routes"], buffer_miles=20, max_cells=200)
    warnings = ["Grid cells approximate a 20-mile route corridor. Forecast values describe sampled model cells, not street-level observations."]
    if plan["mode"] == "live":
        series, weather_warnings = providers.fetch_weather([(cell["center"][1], cell["center"][0]) for cell in cells], departure, departure + timedelta(hours=48))
        warnings.extend(weather_warnings)
    else:
        warnings.append("Synthetic demo corridor forecast; all 49 frames are illustrative.")
    features = []
    unknown = False
    for index, cell in enumerate(cells):
        lon, lat = cell["center"]
        values = {"risks": [], "wind_mph": [], "rain_in_hr": [], "snow_in_hr": []}
        for hour in hours:
            moment = departure + timedelta(hours=hour)
            if plan["mode"] == "demo":
                weather = demo.weather(lat, lon, moment, departure, stored["scenario"])
            else:
                source = series.get(providers.coordinate_key(lat, lon))
                weather = source.at(moment) if source else None
            risk, _ = assess_weather(weather, plan["load_lbs"])
            values["risks"].append(risk)
            unknown |= risk == "unknown"
            for key in ("wind_mph", "rain_in_hr", "snow_in_hr"):
                # JSON null is the only honest missing-value representation.
                # The unknown risk masks it; zero would imply benign weather.
                values[key].append(weather[key] if weather is not None else None)
        features.append({"type": "Feature", "id": index, "geometry": {"type": "Polygon", "coordinates": [cell["polygon"]]}, "properties": values})
    if unknown:
        warnings.append("Unknown cells have no complete forecast for the selected hour and must not be interpreted as low risk.")
    result = {"plan_id": plan_id, "mode": plan["mode"], "start_time": plan["departure"], "hours": hours,
              "resolution_miles": resolution, "geojson": {"type": "FeatureCollection", "features": features}, "warnings": list(dict.fromkeys(warnings))}
    # The plan must still exist; corridor reads never extend its one-hour lifetime.
    cache.set("corridor:" + plan_id, result, settings.PLAN_CACHE_SECONDS)
    return result
