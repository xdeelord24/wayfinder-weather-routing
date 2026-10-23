"""Explicitly synthetic Chicago–Detroit scenarios, never provider observations."""
from datetime import timedelta
from functools import lru_cache
import json
from math import sin
from pathlib import Path

from .domain import RouteData, iso
from .errors import ServiceError

LOCATIONS = [
    {"id": "demo-chicago", "label": "Chicago, IL", "lat": 41.8781, "lon": -87.6298, "timezone": "America/Chicago"},
    {"id": "demo-detroit", "label": "Detroit, MI", "lat": 42.3314, "lon": -83.0458, "timezone": "America/Detroit"},
]


def locations(query):
    value = query.casefold().strip()
    return [dict(location) for location in LOCATIONS if value in location["label"].casefold()]


def selected_locations(origin, destination):
    if origin["id"] != LOCATIONS[0]["id"] or destination["id"] != LOCATIONS[1]["id"]:
        raise ServiceError("demo_locations", "This synthetic demo runs from Chicago, IL to Detroit, MI. Select those endpoints, or use live mode for other US routes.", 400)
    return dict(LOCATIONS[0]), dict(LOCATIONS[1])


@lru_cache(maxsize=1)
def routes():
    snapshot = json.loads((Path(__file__).parent / "data" / "demo_routes.json").read_text(encoding="utf-8"))
    return [RouteData(item["name"], item["coordinates"], item["distances"], item["times"]) for item in snapshot["routes"]]


def weather(lat, lon, moment, departure, scenario="mixed"):
    hour = (moment - departure).total_seconds() / 3600
    phase = 1.2 * sin(hour / 6)
    wind, rain, snow = 12 + phase, 0.0, 0.0
    if scenario == "blocked":
        wind, rain = 58 + phase, .3
    elif scenario == "mixed":
        # Illustrative weather fronts move east after the initial trip window.
        # At +0..6h the saved route scenarios retain their original conditions;
        # by +48h the front has moved 2.52 degrees across the corridor map.
        front_lon = lon - max(0, hour - 6) * .06
        wind, rain = 26 + phase, .12
        if lat > 42.65:
            wind, snow = 58 + phase, 1.2
        elif 42.08 <= lat <= 42.55 and -86.35 < front_lon < -83.55:
            wind, rain = 39 + phase, .06
            if -84.65 < front_lon < -84.05:
                wind = 48 + phase
        elif lat < 41.9 and -85.7 < front_lon < -84.2:
            rain, wind = .65 + .06 * sin(hour / 4), 20 + phase
    # Upper hour marks the preceding-hour precipitation interval.
    forecast_hour = moment.replace(minute=0, second=0, microsecond=0)
    if moment > forecast_hour:
        forecast_hour += timedelta(hours=1)
    return {"wind_mph": wind, "rain_in_hr": rain, "snow_in_hr": snow, "forecast_time": iso(forecast_hour)}
