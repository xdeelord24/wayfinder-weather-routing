"""Pure assessment rules and route geometry. No network or Django dependencies."""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import asin, atan2, ceil, cos, floor, hypot, isfinite, radians, sin, sqrt

MILE_METERS = 1609.344
EARTH_METERS = 6371008.8
RISKS = ("low", "moderate", "high", "severe", "no_travel", "unknown")
SCORES = {risk: index for index, risk in enumerate(RISKS[:-1])}


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def haversine(a, b):
    """Coordinates are always GeoJSON order: longitude, latitude."""
    lon1, lat1, lon2, lat2 = map(radians, (*a, *b))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_METERS * asin(min(1.0, sqrt(h)))


def cumulative_distances(coordinates):
    result = [0.0]
    for a, b in zip(coordinates, coordinates[1:]):
        result.append(result[-1] + haversine(a, b))
    return result


@dataclass
class RouteData:
    name: str
    coordinates: list
    distances: list
    times: list

    @property
    def distance_meters(self):
        return self.distances[-1]

    @property
    def duration_seconds(self):
        return self.times[-1]

    def point_at(self, meters):
        distance = min(max(0.0, meters), self.distance_meters)
        right = max(1, min(len(self.distances) - 1, bisect_left(self.distances, distance)))
        left = right - 1
        span = self.distances[right] - self.distances[left]
        fraction = (distance - self.distances[left]) / span if span else 0
        a, b = self.coordinates[left], self.coordinates[right]
        point = [a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction]
        seconds = self.times[left] + (self.times[right] - self.times[left]) * fraction
        return point, seconds

    def slice(self, start, end):
        first, _ = self.point_at(start)
        last, _ = self.point_at(end)
        inside = self.coordinates[bisect_right(self.distances, start):bisect_left(self.distances, end)]
        return [first, *inside, last]


def assess_weather(weather, load_lbs):
    if weather is None or any(weather.get(key) is None or not isfinite(weather[key]) or weather[key] < 0 for key in ("wind_mph", "rain_in_hr", "snow_in_hr")):
        return "unknown", ["Forecast coverage is unavailable at this arrival time."]
    wind, rain, snow = (weather[key] for key in ("wind_mph", "rain_in_hr", "snow_in_hr"))
    wind_score = 0 if wind < 25 else 1 if wind < 35 else 2 if wind < 45 else 3 if wind < 55 else 4
    rain_score = 0 if rain < .10 else 1 if rain < .25 else 2 if rain < .5 else 3 if rain <= 1 else 4
    snow_score = 0 if snow < .5 else 1 if snow < 1 else 2 if snow < 2 else 3 if snow <= 3 else 4
    reasons = []
    if 45 <= wind < 55 and load_lbs > 30000:
        wind_score = 4
        reasons.append("Wind 45–54.99 mph with a load above 30,000 lb: no travel.")
    elif 35 <= wind < 45 and load_lbs > 40000:
        wind_score = 3
        reasons.append("Wind 35–44.99 mph with a load above 40,000 lb: severe.")
    for label, value, unit, score in (("Wind", wind, "mph", wind_score), ("Rain", rain, "in/hr", rain_score), ("Snow", snow, "in/hr", snow_score)):
        if score:
            reasons.append(f"{label} {value:.2f} {unit}: {RISKS[score].replace('_', ' ')}.")
    return RISKS[max(wind_score, rain_score, snow_score)], reasons or ["Wind, rain, and snow are in the low-risk bands."]


def sample_route(route, spacing_miles, departure, route_id):
    interval = spacing_miles * MILE_METERS
    distances = [index * interval for index in range(int(route.distance_meters // interval) + 1)]
    if route.distance_meters - distances[-1] > .01:
        distances.append(route.distance_meters)
    else:
        distances[-1] = route.distance_meters
    checkpoints = []
    for index, distance in enumerate(distances):
        point, seconds = route.point_at(distance)
        left = 0 if index == 0 else (distances[index - 1] + distance) / 2
        right = route.distance_meters if index == len(distances) - 1 else (distance + distances[index + 1]) / 2
        checkpoints.append({
            "id": f"{route_id}-checkpoint-{index}", "lat": point[1], "lon": point[0],
            "distance_miles": distance / MILE_METERS,
            "eta": iso(departure + timedelta(seconds=seconds)),
            "weather": None, "risk": "unknown", "reasons": [],
            "exposure_miles": (right - left) / MILE_METERS,
        })
    return checkpoints


def finalize_route(route, route_id, checkpoints, departure):
    totals = {risk: 0.0 for risk in RISKS}
    features = []
    for index, checkpoint in enumerate(checkpoints):
        totals[checkpoint["risk"]] += checkpoint["exposure_miles"]
        distance = checkpoint["distance_miles"] * MILE_METERS
        left = 0 if index == 0 else (checkpoints[index - 1]["distance_miles"] * MILE_METERS + distance) / 2
        right = route.distance_meters if index == len(checkpoints) - 1 else (distance + checkpoints[index + 1]["distance_miles"] * MILE_METERS) / 2
        features.append({"type": "Feature", "properties": {"risk": checkpoint["risk"], "checkpoint_id": checkpoint["id"]}, "geometry": {"type": "LineString", "coordinates": route.slice(left, right)}})
    total_miles = route.distance_meters / MILE_METERS
    average = None if totals["unknown"] > 0 else sum(totals[risk] * score for risk, score in SCORES.items()) / total_miles
    return {
        "id": route_id, "name": route.name,
        "geometry": {"type": "LineString", "coordinates": route.coordinates},
        "distance_miles": total_miles, "duration_seconds": route.duration_seconds,
        "arrival": iso(departure + timedelta(seconds=route.duration_seconds)),
        "checkpoints": checkpoints, "segments": {"type": "FeatureCollection", "features": features},
        "summary": {"miles_by_risk": totals, "average_risk": average, "eligible": totals["no_travel"] == 0 and totals["unknown"] == 0},
    }


def recommend(routes):
    eligible = [route for route in routes if route["summary"]["eligible"]]
    if not eligible:
        return None, "No route qualifies: every route contains no-travel conditions or missing forecast coverage. Review the highlighted checkpoints."
    selected = min(eligible, key=lambda route: (
        route["summary"]["miles_by_risk"]["severe"], route["summary"]["miles_by_risk"]["high"],
        route["summary"]["average_risk"], route["duration_seconds"],
    ))
    return selected["id"], "Recommended by least severe-risk mileage, then high-risk mileage, then mileage-weighted risk and travel time. This is an assessment heuristic, not a travel clearance."


def similar_routes(a, b):
    if abs(a.distance_meters - b.distance_meters) / max(a.distance_meters, b.distance_meters) > .08:
        return False
    pairs = [(a.point_at(a.distance_meters * i / 59)[0], b.point_at(b.distance_meters * i / 59)[0]) for i in range(60)]
    return sum(haversine(x, y) < MILE_METERS for x, y in pairs) / len(pairs) >= .9


def _point_segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length_squared = dx * dx + dy * dy
    t = min(1, max(0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length_squared)) if length_squared else 0
    return hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)


def corridor_grid(routes, buffer_miles=20, max_cells=200):
    """Adaptive projected grid; include any cell potentially touching the buffer."""
    # A provider polyline may have 100,000+ vertices. The display and checkpoint
    # timing retain that geometry; corridor inclusion has a separate CPU bound.
    coarse_routes = []
    for route in routes:
        intervals = min(400, max(1, ceil(route.distance_meters / (5 * MILE_METERS))))
        coarse_routes.append([route.point_at(route.distance_meters * i / intervals)[0] for i in range(intervals + 1)])
    all_coords = [point for route in coarse_routes for point in route]
    ref_lat = sum(point[1] for point in all_coords) / len(all_coords)
    ref_lon = sum(point[0] for point in all_coords) / len(all_coords)
    x_scale = EARTH_METERS * cos(radians(ref_lat)) * radians(1)
    y_scale = EARTH_METERS * radians(1)
    project = lambda point: ((point[0] - ref_lon) * x_scale, (point[1] - ref_lat) * y_scale)
    unproject = lambda x, y: [ref_lon + x / x_scale, ref_lat + y / y_scale]
    projected = [[project(point) for point in route] for route in coarse_routes]
    segments = [(a, b) for route in projected for a, b in zip(route, route[1:])]
    points = [point for route in projected for point in route]
    buffer = buffer_miles * MILE_METERS
    xmin, xmax = min(p[0] for p in points) - buffer, max(p[0] for p in points) + buffer
    ymin, ymax = min(p[1] for p in points) - buffer, max(p[1] for p in points) + buffer
    resolution = max(10 * MILE_METERS, sqrt((xmax - xmin) * (ymax - ymin) / 800))
    while True:
        cells = []
        x0, y0 = floor(xmin / resolution) * resolution, floor(ymin / resolution) * resolution
        for i in range(ceil((xmax - x0) / resolution)):
            for j in range(ceil((ymax - y0) / resolution)):
                x, y = x0 + i * resolution, y0 + j * resolution
                center = (x + resolution / 2, y + resolution / 2)
                if min(_point_segment_distance(center, a, b) for a, b in segments) <= buffer + resolution / sqrt(2):
                    coordinates = [unproject(x, y), unproject(x + resolution, y), unproject(x + resolution, y + resolution), unproject(x, y + resolution), unproject(x, y)]
                    cells.append({"center": unproject(*center), "polygon": coordinates})
        if len(cells) <= max_cells:
            return resolution / MILE_METERS, cells
        resolution *= 1.2
