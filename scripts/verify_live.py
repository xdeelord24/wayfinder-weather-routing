"""Bounded, opt-in live provider checks; writes a secret-free JSON evidence record.

Weather only (two HTTP requests): python scripts/verify_live.py
Full service integration: python scripts/verify_live.py --live-plan
The latter needs TOMTOM_API_KEY in the existing server environment or .env.
This checks real adapters/services, not a hosted site's HTTP/browser behavior.
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from threading import Lock
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import httpx
from django.conf import settings
from django.core.cache import cache
from routing import providers, services
from routing.domain import assess_weather, iso
from routing.errors import ServiceError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-plan", action="store_true")
    parser.add_argument("--origin", default="Chicago, Illinois")
    parser.add_argument("--destination", default="Detroit, Michigan")
    parser.add_argument("--spacing", type=int, choices=(10, 25, 50), default=50)
    parser.add_argument("--load", type=float, default=32000)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    evidence = {
        "started_at_utc": iso(now), "status": "incomplete",
        "scope": "live adapters and services; not hosted HTTP or browser verification",
        "tomtom_configured": bool(settings.TOMTOM_API_KEY), "requests": [],
    }
    output = ROOT / "output" / "live-verification"
    output.mkdir(parents=True, exist_ok=True)
    path = output / (now.strftime("%Y%m%dT%H%M%SZ") + ("-plan.json" if args.live_plan else "-weather.json"))
    original_request = providers.request_json
    lock = Lock()

    def measured_request(url, params, timeout=12):
        with lock:
            if len(evidence["requests"]) >= 12:
                raise ServiceError("verification_budget", "The live verification request budget was reached.")
            item = {"provider_host": urlsplit(url).hostname, "started_at_utc": iso(datetime.now(timezone.utc))}
            evidence["requests"].append(item)
        try:
            result = original_request(url, params, timeout)
            item["status"] = "success"
            return result
        except ServiceError as error:
            item.update(status="error", code=error.code)
            raise
        finally:
            item["finished_at_utc"] = iso(datetime.now(timezone.utc))

    providers.request_json = measured_request
    try:
        # The provider's own default time range and HTTP Date independently
        # corroborate the machine clock. No fixture date or forecast override.
        with httpx.Client(timeout=18, follow_redirects=False) as client:
            response = client.get(settings.OPEN_METEO_BASE_URL, params={
                "latitude": 41.8781, "longitude": -87.6298,
                "current": "temperature_2m", "hourly": "wind_speed_10m",
                "forecast_hours": 3, "timezone": "UTC", "timeformat": "unixtime",
                **({"apikey": settings.OPEN_METEO_API_KEY} if settings.OPEN_METEO_API_KEY else {}),
            })
            evidence["provider_clock_probe"] = {"http_status": response.status_code, "http_date": response.headers.get("date")}
            if response.status_code != 200:
                raise ServiceError("clock_probe_failed", "The weather provider clock probe did not return HTTP 200.")
            probe = response.json()
            current = datetime.fromtimestamp(probe["current"]["time"], timezone.utc)
            evidence["provider_clock_probe"].update(current_time_utc=iso(current), clock_difference_seconds=round((now-current).total_seconds()))
            if abs((now-current).total_seconds()) > 3600:
                raise ServiceError("clock_mismatch", "The local clock differs materially from the provider's current data time.")

        departure = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(microsecond=0)
        evidence["departure_utc"] = iso(departure)
        cache.clear()
        if args.live_plan:
            if not settings.TOMTOM_API_KEY:
                raise ServiceError("routing_not_configured", "TOMTOM_API_KEY is not configured; no live routing was attempted.")
            origin = providers.search_locations(args.origin)
            destination = providers.search_locations(args.destination)
            if not origin or not destination:
                raise ServiceError("locations_not_found", "A live origin or destination search returned no US locations.")
            evidence["trip"] = {"origin": origin[0], "destination": destination[0], "load_lbs": args.load, "spacing_miles": args.spacing}
            plan = services.create_plan({"origin": origin[0], "destination": destination[0], "departure": departure,
                                        "load_lbs": args.load, "spacing_miles": args.spacing, "mode": "live"})
            routes = plan["routes"]
            assert 1 <= len(routes) <= 3
            for route in routes:
                points = route["checkpoints"]
                assert points[-1]["eta"] == route["arrival"]
                assert abs(sum(p["exposure_miles"] for p in points) - route["distance_miles"]) < 1e-6
                assert route["summary"]["eligible"] == all(p["risk"] not in {"no_travel", "unknown"} for p in points)
            evidence["plan"] = {"route_count": len(routes), "recommended_route_id": plan["recommended_route_id"], "warnings": plan["warnings"],
                                "routes": [{key: route[key] for key in ("id", "distance_miles", "duration_seconds", "arrival", "summary", "checkpoints")} for route in routes]}
            corridor = services.create_corridor(plan["id"])
            cells = corridor["geojson"]["features"]
            assert corridor["hours"] == list(range(49)) and 0 < len(cells) <= 200
            assert all(len(cell["properties"]["risks"]) == 49 for cell in cells)
            unknown = sum(risk == "unknown" for cell in cells for risk in cell["properties"]["risks"])
            evidence["corridor"] = {"cells": len(cells), "frames": 49, "unknown_cell_hours": unknown, "warnings": corridor["warnings"]}
            assert all(p["weather"] is not None for route in routes for p in route["checkpoints"]), "Live checkpoint forecasts were incomplete"
            assert unknown == 0, "Live corridor forecast coverage was incomplete"
        else:
            # Three actual US coordinates along the Chicago/Gary/Valparaiso area.
            # These are weather probes, not claimed truck route checkpoints.
            coordinates = [(41.8781, -87.6298), (41.5934, -87.3464), (41.4731, -87.0611)]
            sources, warnings = providers.fetch_weather(coordinates, departure, departure + timedelta(hours=48))
            evidence["weather"] = {"warnings": warnings, "locations": []}
            for lat, lon in coordinates:
                source = sources.get(providers.coordinate_key(lat, lon))
                samples = []
                for hour in (0, 1, 24, 48):
                    moment = departure + timedelta(hours=hour)
                    weather = source.at(moment) if source else None
                    samples.append({"time_utc": iso(moment), "weather": weather, "risk": assess_weather(weather, args.load)[0]})
                    assert weather is not None, "A real coordinate/time probe had no complete forecast"
                evidence["weather"]["locations"].append({"lat": lat, "lon": lon, "samples": samples})
        evidence["status"] = "passed"
    except ServiceError as error:
        evidence["status"] = "blocked"
        evidence["error"] = {"code": error.code, "message": str(error)}
    except (AssertionError, KeyError, TypeError, ValueError, httpx.HTTPError) as error:
        # Never serialize URL-bearing network exception text or provider credentials.
        evidence["status"] = "failed"
        evidence["error"] = {"type": type(error).__name__, "message": str(error) if isinstance(error, AssertionError) else "Unexpected live response or network failure; inspect locally."}
    finally:
        providers.request_json = original_request
        evidence["finished_at_utc"] = iso(datetime.now(timezone.utc))
        path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps({"status": evidence["status"], "evidence_path": str(path), "provider_requests": len(evidence["requests"]) + 1,
                          "error": evidence.get("error")}, indent=2))
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
