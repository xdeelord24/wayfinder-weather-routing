"""Network adapters. Provider URLs/credentials never cross the public API boundary."""
from bisect import bisect_left
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from hashlib import sha256
from math import isfinite
from time import monotonic
from urllib.parse import quote

import httpx
from django.conf import settings
from django.core.cache import cache

from .domain import RouteData, cumulative_distances, similar_routes, iso
from .errors import ServiceError


@lru_cache(maxsize=1)
def _timezone_finder():
    from timezonefinder import TimezoneFinder
    return TimezoneFinder()


@lru_cache(maxsize=4096)
def timezone_at(lat, lon):
    name = _timezone_finder().timezone_at(lng=lon, lat=lat)
    if not name:
        raise ServiceError("timezone_unavailable", "A timezone could not be resolved for this location.", 400)
    return name


def request_json(url, params, timeout=12):
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=min(5, timeout)), headers={"User-Agent": "SpotterAssessment/1.0"}, follow_redirects=False) as client:
            response = client.get(url, params=params)
            if response.status_code in (401, 403):
                raise ServiceError("provider_access", "The configured provider rejected access. Check the server API key and provider allowance.", 503)
            if response.status_code == 429:
                raise ServiceError("provider_rate_limit", "The provider request allowance is temporarily exhausted. Please retry later.", 503)
            if response.status_code >= 400:
                raise ServiceError("provider_error", "The provider could not complete this request. Try a different route or retry shortly.")
            return response.json()
    except ServiceError:
        raise
    except httpx.TimeoutException:
        raise ServiceError("provider_timeout", "The provider took too long to respond. Please retry shortly.", 504) from None
    except (httpx.HTTPError, ValueError):
        raise ServiceError("provider_unavailable", "The provider is currently unavailable. Please retry shortly.", 503) from None


def search_locations(query):
    if not settings.TOMTOM_API_KEY:
        raise ServiceError("routing_not_configured", "Live routing needs a TomTom API key on the server. You can explore the clearly labeled demo meanwhile.", 503)
    key = "location-search:" + sha256(query.casefold().encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached
    payload = request_json(f"{settings.TOMTOM_BASE_URL}/search/2/geocode/{quote(query, safe='')}.json", {"key": settings.TOMTOM_API_KEY, "countrySet": "US", "limit": 6, "language": "en-US"})
    locations = []
    for result in payload.get("results", []):
        address = result.get("address", {})
        point = result.get("position", {})
        if address.get("countryCode") != "US" or "lat" not in point or "lon" not in point:
            continue
        lat, lon = float(point["lat"]), float(point["lon"])
        identifier = str(result.get("id") or sha256(f"{lat},{lon}".encode()).hexdigest()[:24])
        location = {"id": identifier, "label": address.get("freeformAddress") or query, "lat": lat, "lon": lon, "timezone": timezone_at(lat, lon)}
        cache.set("location:" + identifier, location, 86400)
        locations.append(location)
    cache.set(key, locations, 3600)
    return locations


def selected_live_location(location):
    saved = cache.get("location:" + location["id"])
    if not saved or abs(saved["lat"] - location["lat"]) > 0.00001 or abs(saved["lon"] - location["lon"]) > 0.00001:
        raise ServiceError("location_expired", "Select the origin and destination from the US search results again; this selection is missing or expired.", 400)
    # Use trusted server geocoding, not caller-supplied label/timezone/country.
    return {**saved, "timezone": timezone_at(saved["lat"], saved["lon"])}


def parse_tomtom_route(data, name):
    try:
        coordinates = [[float(p["longitude"]), float(p["latitude"])] for leg in data["legs"] for p in leg["points"]]
        raw_distances = cumulative_distances(coordinates)
        anchors = sorted(data["progress"], key=lambda item: item["pointIndex"])
        if len(coordinates) < 2 or len(anchors) < 2 or raw_distances[-1] <= 0 or anchors[0]["pointIndex"] != 0 or anchors[-1]["pointIndex"] != len(coordinates) - 1:
            raise ValueError("Missing progress endpoints")
        distances, times = [None] * len(coordinates), [None] * len(coordinates)
        for a, b in zip(anchors, anchors[1:]):
            i, j = int(a["pointIndex"]), int(b["pointIndex"])
            d0, d1 = float(a["distanceInMeters"]), float(b["distanceInMeters"])
            t0, t1 = float(a["travelTimeInSeconds"]), float(b["travelTimeInSeconds"])
            if not (0 <= i < j < len(coordinates) and 0 <= d0 <= d1 and 0 <= t0 <= t1) or not all(isfinite(value) for value in (d0, d1, t0, t1)):
                raise ValueError("Invalid progress")
            span = raw_distances[j] - raw_distances[i]
            for index in range(i, j + 1):
                fraction = (raw_distances[index] - raw_distances[i]) / span if span else (index - i) / (j - i)
                distances[index] = d0 + fraction * (d1 - d0)
                times[index] = t0 + fraction * (t1 - t0)
        if distances[0] != 0 or times[0] != 0 or distances[-1] <= 0 or times[-1] <= 0:
            raise ValueError("Invalid route totals")
        return RouteData(name, coordinates, distances, times)
    except (KeyError, TypeError, ValueError, IndexError):
        raise ServiceError("route_timing_unavailable", "The routing provider did not return usable route geometry and checkpoint travel times. Try again.") from None


def calculate_routes(origin, destination, departure):
    if not settings.TOMTOM_API_KEY:
        raise ServiceError("routing_not_configured", "Live routing needs a TomTom API key on the server. Use demo mode or configure the key.", 503)
    coordinates = f"{origin['lat']},{origin['lon']}:{destination['lat']},{destination['lon']}"
    url = f"{settings.TOMTOM_BASE_URL}/routing/1/calculateRoute/{coordinates}/json"
    common = [("key", settings.TOMTOM_API_KEY), ("travelMode", "truck"), ("departAt", iso(departure)),
              ("traffic", "true"), ("routeRepresentation", "polyline"),
              ("extendedRouteRepresentation", "distance"), ("extendedRouteRepresentation", "travelTime"), ("avoid", "borderCrossings")]
    # Cargo is intentionally never passed as vehicleWeight: gross truck mass is unknown.
    strategies = [
        [("routeType", "fastest"), ("maxAlternatives", "2")],
        [("routeType", "short"), ("maxAlternatives", "0")],
        [("routeType", "fastest"), ("maxAlternatives", "0"), ("avoid", "tollRoads")],
    ]
    routes, warnings = [], []
    deadline = monotonic() + 32
    last_error = None
    for strategy in strategies:
        remaining = deadline - monotonic()
        if remaining < 2:
            warnings.append("Additional route searches reached their time limit; available routes are shown.")
            break
        try:
            data = request_json(url, common + strategy, timeout=min(12, remaining))
            for candidate in data.get("routes", []):
                route = parse_tomtom_route(candidate, f"Route {len(routes) + 1}")
                if not any(similar_routes(route, existing) for existing in routes):
                    routes.append(route)
                if len(routes) == 3:
                    break
        except ServiceError as error:
            last_error = error
            if error.code in {"provider_access", "provider_rate_limit"}:
                break
            warnings.append("One route search was unavailable; successful alternatives are retained.")
        if len(routes) == 3:
            break
    if not routes:
        if last_error:
            raise last_error
        raise ServiceError("no_routes", "No drivable route was found between these US locations. Try different endpoints.", 422)
    if len(routes) < 3:
        warnings.append(f"The provider returned {len(routes)} distinct route(s) after bounded alternative searches. Three alternatives are not always available.")
    warnings.append("Truck profile used without gross vehicle weight or dimensions. Cargo load affects weather risk only; vehicle clearance and weight restrictions are not verified.")
    return routes, list(dict.fromkeys(warnings))


def coordinate_key(lat, lon):
    return f"{lat:.4f},{lon:.4f}"


class WeatherSeries:
    def __init__(self, payload):
        hourly = payload.get("hourly", {})
        if not isinstance(hourly, dict):
            hourly = {}
        self.times = hourly.get("time", [])
        self.wind = hourly.get("wind_speed_10m", [])
        self.rain = hourly.get("rain", [])
        self.showers = hourly.get("showers", [])
        self.snow = hourly.get("snowfall", [])
        if not isinstance(self.times, list) or any(not isinstance(value, (float, int)) or not isfinite(value) for value in self.times) or any(b <= a for a, b in zip(self.times, self.times[1:])):
            self.times = []
        for attr in ("wind", "rain", "showers", "snow"):
            if not isinstance(getattr(self, attr), list):
                setattr(self, attr, [])

    def at(self, moment):
        stamp = moment.timestamp()
        if not self.times or stamp < self.times[0] or stamp > self.times[-1]:
            return None
        right = bisect_left(self.times, stamp)
        left = right if self.times[right] == stamp else max(0, right - 1)
        try:
            values = (self.wind[left], self.wind[right], self.rain[right], self.showers[right], self.snow[right])
            if any(value is None or not isinstance(value, (int, float)) or not isfinite(value) or value < 0 for value in values):
                return None
            fraction = (stamp - self.times[left]) / (self.times[right] - self.times[left]) if left != right else 0
            wind = self.wind[left] + fraction * (self.wind[right] - self.wind[left])
            # Remove binary conversion noise at exact policy boundaries, e.g.
            # 72.42048 km/h must classify as 45 mph, not 44.99999999999999.
            return {"wind_mph": round(wind / 1.609344, 10),
                    "rain_in_hr": round((self.rain[right] + self.showers[right]) / 25.4, 10),
                    "snow_in_hr": round(self.snow[right] / 2.54, 10),
                    "forecast_time": iso(datetime.fromtimestamp(self.times[right], timezone.utc))}
        except (IndexError, TypeError, ValueError):
            return None


def fetch_weather(coordinates, start, end):
    """Batch coordinates, cache source hourly series, and preserve missing coverage."""
    unique = {coordinate_key(lat, lon): (lat, lon) for lat, lon in coordinates}
    start_hour = (start - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    end_hour = (end + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    window = f"{start_hour.isoformat()}:{end_hour.isoformat()}"
    found, missing, warnings = {}, [], []
    for key, point in unique.items():
        cache_key = "weather:" + sha256(f"{key}:{window}".encode()).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            found[key] = WeatherSeries(cached)
        else:
            missing.append((key, point, cache_key))

    def fetch_chunk(chunk):
        params = {"latitude": ",".join(str(item[1][0]) for item in chunk), "longitude": ",".join(str(item[1][1]) for item in chunk),
                  "hourly": "wind_speed_10m,rain,showers,snowfall", "wind_speed_unit": "kmh", "precipitation_unit": "mm",
                  "timeformat": "unixtime", "timezone": "UTC", "start_hour": start_hour.strftime("%Y-%m-%dT%H:%M"), "end_hour": end_hour.strftime("%Y-%m-%dT%H:%M")}
        if settings.OPEN_METEO_API_KEY:
            params["apikey"] = settings.OPEN_METEO_API_KEY
        data = request_json(settings.OPEN_METEO_BASE_URL, params, timeout=18)
        responses = data if isinstance(data, list) else [data]
        if len(responses) != len(chunk):
            raise ServiceError("weather_invalid", "The weather provider returned an incomplete batch.")
        return list(zip(chunk, responses))

    chunks = [missing[index:index + 50] for index in range(0, len(missing), 50)]
    pool = ThreadPoolExecutor(max_workers=3)
    futures = [pool.submit(fetch_chunk, chunk) for chunk in chunks]
    try:
        for future in as_completed(futures, timeout=40):
            try:
                for (key, _, cache_key), payload in future.result():
                    if not isinstance(payload, dict):
                        continue
                    found[key] = WeatherSeries(payload)
                    cache.set(cache_key, payload, 1800)
            except ServiceError:
                warnings.append("Some weather forecasts could not be loaded. Missing cells/checkpoints are marked unknown and cannot qualify for recommendation.")
    except TimeoutError:
        warnings.append("The forecast time budget was reached. Available weather is retained; unfinished cells/checkpoints are unknown.")
    finally:
        # Do not wait for the whole queued batch: at most three in-flight calls
        # finish within their individual timeout; queued work is cancelled.
        pool.shutdown(wait=False, cancel_futures=True)
    return found, list(dict.fromkeys(warnings))
