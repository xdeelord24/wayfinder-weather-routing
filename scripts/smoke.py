"""Exercise the running HTTP API without credentials or mocked HTTP responses.

Usage: python scripts/smoke.py [http://127.0.0.1:8000] [--frontend]
These are explicit synthetic demo scenarios, not live routing verification.
"""
import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8000")
parser.add_argument("--frontend", action="store_true", help="Also verify the served production HTML and its entry assets")
args = parser.parse_args()
BASE_URL = args.base_url.rstrip("/")


def check_frontend():
    with urllib.request.urlopen(BASE_URL + "/", timeout=15) as response:
        html = response.read().decode()
        assert response.status == 200 and "Wayfinder" in html
    assets = set(re.findall(r'(?:src|href)="(/assets/[^" ]+\.(?:js|css))"', html))
    assert any(path.endswith(".js") for path in assets)
    assert any(path.endswith(".css") for path in assets)
    for path in assets:
        with urllib.request.urlopen(BASE_URL + path, timeout=15) as response:
            mime = response.headers.get_content_type()
            assert response.status == 200 and len(response.read()) > 0
            assert mime in {"text/javascript", "application/javascript", "text/css"}, (path, mime)
    return len(assets)


def request(path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE_URL + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise AssertionError(f"{path}: HTTP {error.code}: {error.read().decode()}") from error


def main():
    assets = check_frontend() if args.frontend else None
    health = request("/api/health")
    assert health["status"] == "ok"
    chicago = request("/api/locations?q=Chicago&mode=demo")["locations"][0]
    detroit = request("/api/locations?q=Detroit&mode=demo")["locations"][0]
    departure = datetime.now(timezone.utc) + timedelta(hours=1)
    results = []
    for scenario, spacing in [("mixed", 25), ("clear", 10), ("blocked", 50)]:
        plan = request("/api/plan", {
            "origin": chicago, "destination": detroit,
            "departure": departure.isoformat(), "load_lbs": 32000,
            "spacing_miles": spacing, "mode": "demo", "scenario": scenario,
        })
        assert plan["mode"] == "demo" and len(plan["routes"]) == 3
        assert len({route["id"] for route in plan["routes"]}) == 3
        for route in plan["routes"]:
            points = route["checkpoints"]
            assert len(points) >= 2
            assert abs(sum(point["exposure_miles"] for point in points) - route["distance_miles"]) < 1e-6
            assert abs(sum(route["summary"]["miles_by_risk"].values()) - route["distance_miles"]) < 1e-6
            assert points[0]["distance_miles"] == 0
            assert abs(points[-1]["distance_miles"] - route["distance_miles"]) < 1e-6
            times = [datetime.fromisoformat(point["eta"].replace("Z", "+00:00")) for point in points]
            assert times == sorted(times)
            assert points[-1]["eta"] == route["arrival"]
            if route["summary"]["eligible"]:
                assert all(point["risk"] not in {"no_travel", "unknown"} for point in points)
        if scenario == "blocked":
            assert plan["recommended_route_id"] is None
            assert not any(route["summary"]["eligible"] for route in plan["routes"])
        else:
            chosen = next(route for route in plan["routes"] if route["id"] == plan["recommended_route_id"])
            assert chosen["summary"]["eligible"]
        corridor = request("/api/corridor", {"plan_id": plan["id"]})
        assert corridor["hours"] == list(range(49))
        cells = corridor["geojson"]["features"]
        assert 0 < len(cells) <= 200
        assert all(len(cell["properties"]["risks"]) == 49 for cell in cells)
        changed_cells = sum(cell["properties"]["risks"][0] != cell["properties"]["risks"][48] for cell in cells)
        if scenario == "mixed":
            assert changed_cells >= 5, "The mixed demo must show weather moving across the corridor"
        results.append({"scenario": scenario, "spacing_miles": spacing,
                        "routes": len(plan["routes"]), "corridor_cells": len(cells),
                        "cells_changing_risk_by_48h": changed_cells,
                        "recommended_route_id": plan["recommended_route_id"]})
    print(json.dumps({"base_url": BASE_URL, "status": "passed", "live_routing_configured": health.get("routing_configured"),
                      "scope": "synthetic demo HTTP integration", "frontend_entry_assets": assets, "results": results}, indent=2))


if __name__ == "__main__":
    main()
