"""Verify one real trip through a deployed Wayfinder HTTPS origin.

Usage: python scripts/verify_hosted.py https://your-public-hostname
At most six requests, no retries: health, frontend, two location searches,
one live plan, and its 49-frame corridor. No credentials are accepted or saved.
This is HTTP verification, not a substitute for a visible browser walkthrough.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from math import isfinite
from pathlib import Path
import re
from urllib.parse import urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
WEATHER_FIELDS = ("wind_mph", "rain_in_hr", "snow_in_hr")
RISKS = {"low", "moderate", "high", "severe", "no_travel", "unknown"}


def iso(moment):
    return moment.isoformat().replace("+00:00", "Z")


def timestamp(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert moment.tzinfo is not None, "A timestamp did not identify its timezone"
    return moment.astimezone(timezone.utc)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="Public HTTPS origin, without credentials, query or path")
    parser.add_argument("--origin", default="Chicago, Illinois")
    parser.add_argument("--destination", default="Detroit, Michigan")
    parser.add_argument("--spacing", type=int, choices=(10, 25, 50), default=50)
    parser.add_argument("--load", type=float, default=32000)
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ("", "/"):
        parser.error("Use only a public HTTPS origin, without credentials, query, fragment or path.")
    if not number(args.load) or args.load < 0:
        parser.error("Cargo load must be finite and nonnegative.")
    base_url = args.base_url.rstrip("/")
    now = datetime.now(timezone.utc)
    evidence = {"started_at_utc": iso(now), "base_url": base_url, "status": "incomplete",
                "scope": "hosted frontend HTML and live HTTP API; browser rendering not checked", "requests": []}
    output = ROOT / "output" / "live-verification"
    output.mkdir(parents=True, exist_ok=True)
    path = output / (now.strftime("%Y%m%dT%H%M%SZ") + "-hosted.json")

    with httpx.Client(timeout=httpx.Timeout(90, connect=10), follow_redirects=False, headers={"User-Agent": "WayfinderAssessmentVerification/1.0"}) as client:
        def request(endpoint, *, params=None, body=None, html=False):
            require(len(evidence["requests"]) < 6, "The six-request verification budget was reached")
            record = {"endpoint": endpoint, "method": "GET" if body is None else "POST", "started_at_utc": iso(datetime.now(timezone.utc))}
            evidence["requests"].append(record)
            try:
                response = client.get(base_url + endpoint, params=params) if body is None else client.post(base_url + endpoint, json=body)
                record.update(http_status=response.status_code, server_date=response.headers.get("date"))
                if response.status_code != 200:
                    # Store only the public error code, never full responses,
                    # redirect URLs, exception URLs or authentication headers.
                    try:
                        code = response.json().get("error", {}).get("code", "")
                        if isinstance(code, str) and re.fullmatch(r"[a-z_]{1,80}", code):
                            record["error_code"] = code
                    except (ValueError, AttributeError, TypeError):
                        pass
                    raise AssertionError(f"{endpoint} returned HTTP {response.status_code}")
                content_type = response.headers.get("content-type", "").lower()
                if html:
                    require("text/html" in content_type, "The frontend did not return HTML")
                    return response.text
                require("application/json" in content_type, f"{endpoint} did not return JSON")
                return response.json()
            finally:
                record["finished_at_utc"] = iso(datetime.now(timezone.utc))

        try:
            health = request("/api/health")
            evidence["health"] = {"status": health.get("status"), "routing_configured": health.get("routing_configured")}
            require(health.get("status") == "ok" and health.get("routing_configured") is True, "Hosted health must be OK with live routing configured")
            html = request("/", html=True)
            require(re.search(r"<title>[^<]*Wayfinder[^<]*</title>", html, re.I), "The frontend title is not Wayfinder")
            assets = sorted(set(re.findall(r'(?:src|href)="(/assets/[^" ]+\.(?:js|css))"', html)))
            require(any(asset.endswith(".js") for asset in assets) and any(asset.endswith(".css") for asset in assets), "Built frontend JS/CSS references were not found")
            evidence["frontend"] = {"title_verified": True, "entry_asset_references": assets, "asset_bodies_requested": False}
            origin_results = request("/api/locations", params={"q": args.origin, "mode": "live"})["locations"]
            destination_results = request("/api/locations", params={"q": args.destination, "mode": "live"})["locations"]
            require(bool(origin_results and destination_results), "A live location search returned no results")
            origin, destination = origin_results[0], destination_results[0]
            require(bool(origin.get("id") and destination.get("id")), "Server-selected location IDs were missing")
            departure = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(microsecond=0)
            evidence["trip"] = {"origin": origin, "destination": destination, "departure_utc": iso(departure),
                                "load_lbs": args.load, "spacing_miles": args.spacing, "location_source": "first result of each hosted live search"}
            plan = request("/api/plan", body={"origin": origin, "destination": destination, "departure": iso(departure),
                                             "load_lbs": args.load, "spacing_miles": args.spacing, "mode": "live"})
            require(plan["mode"] == "live", "The hosted plan was not marked live")
            require(timestamp(plan["departure"]) == departure, "The plan departure changed")
            routes = plan["routes"]
            require(1 <= len(routes) <= 3, "Expected one to three live alternatives")
            require(len({route["id"] for route in routes}) == len(routes), "Duplicate live route IDs")
            require(len({json.dumps(route["geometry"], sort_keys=True) for route in routes}) == len(routes), "Identical route geometries were returned as alternatives")
            summaries = []
            for route in routes:
                points = route["checkpoints"]
                require(len(points) >= 2, "A route did not include origin and destination checkpoints")
                require(number(route["distance_miles"]) and route["distance_miles"] > 0, "Route mileage was invalid")
                require(number(route["duration_seconds"]) and route["duration_seconds"] > 0, "Route duration was invalid")
                require(abs(sum(point["exposure_miles"] for point in points) - route["distance_miles"]) < 1e-6, "Checkpoint exposure did not conserve route mileage")
                require(abs(sum(route["summary"]["miles_by_risk"].values()) - route["distance_miles"]) < 1e-6, "Risk exposure did not conserve route mileage")
                require(points[0]["distance_miles"] == 0 and abs(points[-1]["distance_miles"] - route["distance_miles"]) < 1e-6, "Route endpoints were missing")
                arrivals = [timestamp(point["eta"]) for point in points]
                require(arrivals == sorted(arrivals), "Checkpoint ETAs were not ordered")
                require(arrivals[-1] == timestamp(route["arrival"]), "Final checkpoint did not match route arrival")
                require(abs((arrivals[-1] - departure).total_seconds() - route["duration_seconds"]) < .001, "Arrival time did not match the route duration")
                for point, arrival in zip(points, arrivals):
                    weather = point["weather"]
                    require(isinstance(weather, dict) and all(number(weather.get(field)) and weather[field] >= 0 for field in WEATHER_FIELDS), "A checkpoint lacked complete live wind/rain/snow forecasts")
                    delta = (timestamp(weather["forecast_time"]) - arrival).total_seconds()
                    require(0 <= delta < 3600.001, "A checkpoint forecast did not cover its arrival interval")
                    require(point["risk"] in RISKS - {"unknown"}, "A live checkpoint risk was unknown or invalid")
                eligible = all(point["risk"] not in {"unknown", "no_travel"} for point in points)
                require(route["summary"]["eligible"] == eligible, "Route eligibility did not match checkpoint hazards")
                summaries.append({key: route[key] for key in ("id", "distance_miles", "duration_seconds", "arrival", "summary", "checkpoints")})
            selected = plan["recommended_route_id"]
            if selected is not None:
                require(any(route["id"] == selected and route["summary"]["eligible"] for route in routes), "Recommended route was missing or ineligible")
            else:
                require(not any(route["summary"]["eligible"] for route in routes), "An eligible route existed without a recommendation")
            evidence["plan"] = {"route_count": len(routes), "three_route_example_verified": len(routes) == 3,
                                "recommended_route_id": selected, "routes": summaries, "warnings": plan["warnings"]}
            corridor = request("/api/corridor", body={"plan_id": plan["id"]})
            require(corridor["mode"] == "live" and corridor["plan_id"] == plan["id"], "Corridor did not belong to the live plan")
            require(corridor["hours"] == list(range(49)), "Corridor did not contain +0 through +48 hours")
            require(timestamp(corridor["start_time"]) == departure, "Corridor time origin did not match departure")
            cells = corridor["geojson"]["features"]
            require(0 < len(cells) <= 200, "Corridor cell count was outside its documented bound")
            unknown = 0
            for cell in cells:
                props = cell["properties"]
                require(all(len(props[field]) == 49 for field in (*WEATHER_FIELDS, "risks")), "A corridor cell was missing hourly values")
                require(all(number(value) and value >= 0 for field in WEATHER_FIELDS for value in props[field]), "A corridor cell lacked complete live forecasts")
                require(all(risk in RISKS for risk in props["risks"]), "A corridor risk value was invalid")
                unknown += props["risks"].count("unknown")
            evidence["corridor"] = {"cells": len(cells), "frames": 49, "unknown_cell_hours": unknown, "warnings": corridor["warnings"]}
            require(unknown == 0, "Some live corridor forecast hours remained unknown")
            evidence["status"] = "passed" if len(routes) == 3 else "passed_with_route_shortfall"
            if len(routes) < 3:
                evidence["limitation"] = "The live provider returned fewer than three distinct routes; a three-route live example is not verified."
        except (AssertionError, KeyError, TypeError, ValueError, httpx.HTTPError) as error:
            evidence["status"] = "failed"
            evidence["error"] = {"type": type(error).__name__, "message": str(error) if isinstance(error, AssertionError) else "Unexpected live response or network failure; inspect the last recorded endpoint locally."}
        finally:
            evidence["finished_at_utc"] = iso(datetime.now(timezone.utc))
            path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            print(json.dumps({"status": evidence["status"], "evidence_path": str(path), "requests": len(evidence["requests"]),
                              "error": evidence.get("error"), "limitation": evidence.get("limitation")}, indent=2))
    return 0 if evidence["status"].startswith("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
