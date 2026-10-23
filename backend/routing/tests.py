from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from . import demo, providers, services
from .domain import MILE_METERS, RISKS, RouteData, assess_weather, corridor_grid, finalize_route, recommend, sample_route, similar_routes
from .errors import ServiceError


def weather(wind=0, rain=0, snow=0):
    return {"wind_mph": wind, "rain_in_hr": rain, "snow_in_hr": snow, "forecast_time": "2026-10-23T00:00:00Z"}


def plan_input(scenario="mixed", load=20000, spacing=25):
    return {"origin": dict(demo.LOCATIONS[0]), "destination": dict(demo.LOCATIONS[1]),
            "departure": datetime.now(timezone.utc) + timedelta(hours=1), "load_lbs": load,
            "spacing_miles": spacing, "mode": "demo", "scenario": scenario}


class RiskTests(SimpleTestCase):
    def test_wind_boundaries(self):
        for wind, expected in ((24.99, "low"), (25, "moderate"), (34.99, "moderate"), (35, "high"), (44.99, "high"), (45, "severe"), (54.99, "severe"), (55, "no_travel")):
            with self.subTest(wind=wind):
                self.assertEqual(assess_weather(weather(wind=wind), 0)[0], expected)

    def test_rain_boundaries(self):
        for rain, expected in ((.099, "low"), (.10, "moderate"), (.249, "moderate"), (.25, "high"), (.499, "high"), (.5, "severe"), (1, "severe"), (1.001, "no_travel")):
            with self.subTest(rain=rain):
                self.assertEqual(assess_weather(weather(rain=rain), 0)[0], expected)

    def test_snow_boundaries(self):
        for snow, expected in ((.499, "low"), (.5, "moderate"), (.999, "moderate"), (1, "high"), (1.999, "high"), (2, "severe"), (3, "severe"), (3.001, "no_travel")):
            with self.subTest(snow=snow):
                self.assertEqual(assess_weather(weather(snow=snow), 0)[0], expected)

    def test_load_rules_are_strict(self):
        self.assertEqual(assess_weather(weather(wind=45), 30000)[0], "severe")
        self.assertEqual(assess_weather(weather(wind=45), 30000.01)[0], "no_travel")
        self.assertEqual(assess_weather(weather(wind=35), 40000)[0], "high")
        self.assertEqual(assess_weather(weather(wind=35), 40000.01)[0], "severe")
        self.assertEqual(assess_weather(weather(wind=34.99), 100000)[0], "moderate")

    def test_max_hazard_and_unknown(self):
        self.assertEqual(assess_weather(weather(wind=26, rain=.3, snow=2.5), 0)[0], "severe")
        self.assertEqual(assess_weather(None, 0)[0], "unknown")
        self.assertEqual(assess_weather(weather(wind=float("nan")), 0)[0], "unknown")
        self.assertEqual(assess_weather(weather(rain=-1), 0)[0], "unknown")


class SamplingTests(SimpleTestCase):
    def setUp(self):
        self.departure = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
        self.route = RouteData("Variable speed", [[-87, 42], [-86.5, 42], [-86, 42]], [0, 25 * MILE_METERS, 60 * MILE_METERS], [0, 3600, 5400])

    def test_endpoint_midpoint_exposure_and_nonuniform_eta(self):
        points = sample_route(self.route, 25, self.departure, "r")
        self.assertEqual([round(p["distance_miles"]) for p in points], [0, 25, 50, 60])
        self.assertEqual([round(p["exposure_miles"]) for p in points], [12, 25, 18, 5])
        self.assertAlmostEqual(sum(p["exposure_miles"] for p in points), 60)
        self.assertEqual(points[1]["eta"], "2026-10-23T13:00:00Z")
        self.assertNotEqual(points[1]["eta"], "2026-10-23T12:37:30Z")

    def test_short_route_endpoints(self):
        route = RouteData("Short", [[-87, 42], [-86.99, 42]], [0, 3 * MILE_METERS], [0, 300])
        points = sample_route(route, 10, self.departure, "r")
        self.assertEqual(len(points), 2)
        self.assertEqual([p["exposure_miles"] for p in points], [1.5, 1.5])

    def test_unknown_and_no_travel_are_excluded(self):
        for risk in ("unknown", "no_travel"):
            points = sample_route(self.route, 25, self.departure, "r")
            for point in points:
                point["risk"] = "low"
            points[1]["risk"] = risk
            result = finalize_route(self.route, "r", points, self.departure)
            self.assertFalse(result["summary"]["eligible"])
            self.assertEqual(recommend([result])[0], None)
            self.assertAlmostEqual(sum(result["summary"]["miles_by_risk"].values()), result["distance_miles"])
            self.assertEqual(set(result["summary"]["miles_by_risk"]), set(RISKS))

    def test_ranking_uses_severe_before_average_or_time(self):
        route = {"id": "faster", "duration_seconds": 20, "summary": {"eligible": True, "miles_by_risk": {"severe": 1, "high": 0}, "average_risk": .01}}
        safer = {"id": "safer", "duration_seconds": 100, "summary": {"eligible": True, "miles_by_risk": {"severe": 0, "high": 10}, "average_risk": 2}}
        self.assertEqual(recommend([route, safer])[0], "safer")

    def test_duplicate_routes(self):
        self.assertTrue(similar_routes(self.route, self.route))
        other = RouteData("Other", [[-87, 44], [-86.5, 44], [-86, 44]], self.route.distances, self.route.times)
        self.assertFalse(similar_routes(self.route, other))


class WeatherTests(SimpleTestCase):
    def source(self, **changes):
        values = {"time": [0, 3600, 7200], "wind_speed_10m": [16.09344, 32.18688, 48.28032], "rain": [0, 2.54, 5.08], "showers": [0, 2.54, 0], "snowfall": [0, 2.54, 5.08]}
        values.update(changes)
        return providers.WeatherSeries({"hourly": values})

    def test_interpolation_units_and_precipitation_interval(self):
        result = self.source().at(datetime.fromtimestamp(1800, timezone.utc))
        self.assertAlmostEqual(result["wind_mph"], 15)
        self.assertAlmostEqual(result["rain_in_hr"], .2)
        self.assertAlmostEqual(result["snow_in_hr"], 1)
        self.assertEqual(result["forecast_time"], "1970-01-01T01:00:00Z")

    def test_exact_hour_and_range(self):
        self.assertAlmostEqual(self.source().at(datetime.fromtimestamp(3600, timezone.utc))["wind_mph"], 20)
        self.assertIsNone(self.source().at(datetime.fromtimestamp(7201, timezone.utc)))
        self.assertIsNone(self.source().at(datetime.fromtimestamp(-1, timezone.utc)))

    def test_unit_conversion_preserves_exact_wind_policy_boundary(self):
        source = self.source(wind_speed_10m=[72.42048] * 3)
        result = source.at(datetime.fromtimestamp(3600, timezone.utc))
        self.assertEqual(result["wind_mph"], 45)
        self.assertEqual(assess_weather(result, 30001)[0], "no_travel")

    def test_missing_or_malformed_data_is_unknown(self):
        for changes in ({"rain": [0, None, 0]}, {"wind_speed_10m": []}, {"time": ["bad"]}, {"time": [0, 3600, 3000]}, {"time": None}):
            self.assertIsNone(self.source(**changes).at(datetime.fromtimestamp(1800, timezone.utc)))

    @patch("routing.providers.as_completed", side_effect=TimeoutError)
    @patch("routing.providers.request_json", return_value={"hourly": {}})
    def test_overall_weather_budget_preserves_missing_coverage(self, request, completed):
        cache.clear()
        now = datetime.now(timezone.utc)
        sources, warnings = providers.fetch_weather([(42, -87)], now, now + timedelta(hours=1))
        self.assertEqual(sources, {})
        self.assertTrue(any("time budget" in warning for warning in warnings))


@override_settings(TOMTOM_API_KEY="test-secret")
class ProviderTests(SimpleTestCase):
    def route_data(self):
        return {"legs": [{"points": [{"longitude": -87, "latitude": 42}, {"longitude": -86.5, "latitude": 42}, {"longitude": -86, "latitude": 42}]}],
                "progress": [{"pointIndex": 0, "distanceInMeters": 0, "travelTimeInSeconds": 0}, {"pointIndex": 1, "distanceInMeters": 20000, "travelTimeInSeconds": 3000}, {"pointIndex": 2, "distanceInMeters": 40000, "travelTimeInSeconds": 4000}]}

    def test_provider_progress_used(self):
        route = providers.parse_tomtom_route(self.route_data(), "r")
        self.assertEqual(route.point_at(20000)[1], 3000)
        self.assertEqual(route.point_at(30000)[1], 3500)

    def test_missing_progress_rejected(self):
        value = self.route_data()
        del value["progress"]
        with self.assertRaises(ServiceError):
            providers.parse_tomtom_route(value, "r")

    @patch("routing.providers.request_json")
    def test_bounded_search_deduplication_and_no_cargo_weight(self, request):
        request.return_value = {"routes": [self.route_data(), self.route_data()]}
        routes, warnings = providers.calculate_routes(demo.LOCATIONS[0], demo.LOCATIONS[1], datetime.now(timezone.utc))
        self.assertEqual(len(routes), 1)
        self.assertEqual(request.call_count, 3)
        self.assertTrue(any("1 distinct" in item for item in warnings))
        for call in request.call_args_list:
            params = call.args[1]
            self.assertNotIn("vehicleWeight", dict(params))
            self.assertEqual(dict(params)["travelMode"], "truck")
            self.assertIn(("extendedRouteRepresentation", "travelTime"), params)

    @patch("routing.providers.request_json", side_effect=ServiceError("provider_timeout", "Timeout", 504))
    def test_errors_do_not_expose_key(self, request):
        with self.assertRaises(ServiceError) as caught:
            providers.calculate_routes(demo.LOCATIONS[0], demo.LOCATIONS[1], datetime.now(timezone.utc))
        self.assertNotIn("test-secret", str(caught.exception))
        self.assertEqual(request.call_count, 3)

    def test_selected_timezone_is_server_derived(self):
        cache.clear()
        location = dict(demo.LOCATIONS[0])
        cache.set("location:" + location["id"], location)
        location["timezone"] = "Asia/Manila"
        self.assertEqual(providers.selected_live_location(location)["timezone"], "America/Chicago")


class APITests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def post_plan(self, **changes):
        data = plan_input()
        data["departure"] = data["departure"].isoformat()
        data.update(changes)
        return self.client.post("/api/plan", data, format="json")

    def test_health_and_demo_search(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        response = self.client.get("/api/locations", {"q": "Chicago", "mode": "demo"})
        self.assertEqual(response.json()["locations"][0]["timezone"], "America/Chicago")

    def test_three_distinct_demo_routes_and_contract(self):
        response = self.post_plan()
        self.assertEqual(response.status_code, 200, response.content)
        plan = response.json()
        self.assertEqual(plan["mode"], "demo")
        self.assertEqual(len(plan["routes"]), 3)
        self.assertEqual(len({str(route["geometry"]) for route in plan["routes"]}), 3)
        self.assertEqual(plan["timezone"], "America/Chicago")
        self.assertTrue(any("synthetic weather" in text for text in plan["warnings"]))
        self.assertIsNotNone(plan["recommended_route_id"])
        for route in plan["routes"]:
            self.assertAlmostEqual(sum(point["exposure_miles"] for point in route["checkpoints"]), route["distance_miles"])
            self.assertEqual(route["geometry"]["type"], "LineString")

    def test_blocked_and_clear_scenarios(self):
        blocked = self.post_plan(scenario="blocked").json()
        self.assertIsNone(blocked["recommended_route_id"])
        self.assertTrue(all(not route["summary"]["eligible"] for route in blocked["routes"]))
        clear = self.post_plan(scenario="clear").json()
        self.assertIsNotNone(clear["recommended_route_id"])
        self.assertTrue(all(route["summary"]["average_risk"] == 0 for route in clear["routes"]))

    def test_load_changes_synthetic_risk(self):
        light = self.post_plan(load_lbs=20000).json()
        heavy = self.post_plan(load_lbs=45000).json()
        self.assertNotEqual([route["summary"] for route in light["routes"]], [route["summary"] for route in heavy["routes"]])
        self.assertNotEqual(light["recommended_route_id"], heavy["recommended_route_id"])
        self.assertEqual(light["recommended_route_id"], "route-1")
        self.assertEqual(heavy["recommended_route_id"], "route-3")

    def test_mixed_front_moves_across_several_corridor_cells_after_trip(self):
        plan = self.post_plan(load_lbs=45000).json()
        result = self.client.post("/api/corridor", {"plan_id": plan["id"]}, format="json").json()
        frames = [feature["properties"]["risks"] for feature in result["geojson"]["features"]]
        self.assertGreaterEqual(sum(frame[0] != frame[24] for frame in frames), 5)
        self.assertGreaterEqual(sum(frame[0] != frame[48] for frame in frames), 5)
        self.assertEqual(plan["recommended_route_id"], "route-3")

    def test_clear_and_blocked_stay_in_their_bands_at_future_hours(self):
        departure = datetime.now(timezone.utc)
        for hour in (0, 6, 24, 48):
            moment = departure + timedelta(hours=hour)
            self.assertEqual(assess_weather(demo.weather(42.3, -84.3, moment, departure, "clear"), 45000)[0], "low")
            self.assertEqual(assess_weather(demo.weather(42.3, -84.3, moment, departure, "blocked"), 0)[0], "no_travel")

    def test_corridor_has_49_departure_anchored_frames_and_cache(self):
        plan = self.post_plan().json()
        response = self.client.post("/api/corridor", {"plan_id": plan["id"]}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()
        self.assertEqual(result["start_time"], plan["departure"])
        self.assertEqual(result["hours"], list(range(49)))
        self.assertTrue(0 < len(result["geojson"]["features"]) <= 200)
        for feature in result["geojson"]["features"]:
            self.assertEqual(feature["geometry"]["coordinates"][0][0], feature["geometry"]["coordinates"][0][-1])
            for field in ("risks", "wind_mph", "rain_in_hr", "snow_in_hr"):
                self.assertEqual(len(feature["properties"][field]), 49)
        with patch("routing.services.corridor_grid", side_effect=AssertionError("Must use cache")):
            repeated = self.client.post("/api/corridor", {"plan_id": plan["id"]}, format="json")
            self.assertEqual(repeated.json(), result)

    def test_plan_expiry_checked_before_corridor_cache(self):
        cache.set("corridor:expired", {"cached": True})
        response = self.client.post("/api/corridor", {"plan_id": "expired"}, format="json")
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()["error"]["code"], "plan_expired")

    def test_validation_and_error_envelope(self):
        for changes in ({"departure": "2026-10-23T12:00"}, {"departure": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()}, {"load_lbs": -1}, {"spacing_miles": 15}, {"mode": "fake"}):
            with self.subTest(changes=changes):
                response = self.post_plan(**changes)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.json()["error"]), {"code", "message"})

    def test_current_minute_and_caller_timezone(self):
        origin = {**demo.LOCATIONS[0], "timezone": "Asia/Manila"}
        response = self.post_plan(origin=origin, departure=datetime.now(timezone.utc).replace(second=0, microsecond=0).isoformat())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["timezone"], "America/Chicago")

    @override_settings(TOMTOM_API_KEY="")
    def test_no_key_and_missing_endpoint(self):
        response = self.client.get("/api/locations", {"q": "Chicago", "mode": "live"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "routing_not_configured")
        self.assertEqual(self.client.get("/api/health/").status_code, 404)
        self.assertEqual(self.client.get("/api/missing").json()["error"]["code"], "not_found")

    @patch("routing.services.providers.fetch_weather", return_value=({}, ["Provider unavailable"]))
    def test_missing_corridor_weather_is_null_and_unknown(self, fetch):
        plan = self.post_plan().json()
        stored = cache.get("plan:" + plan["id"])
        stored["response"]["mode"] = "live"
        cache.set("plan:" + plan["id"], stored)
        result = self.client.post("/api/corridor", {"plan_id": plan["id"]}, format="json").json()
        for feature in result["geojson"]["features"]:
            self.assertEqual(set(feature["properties"]["risks"]), {"unknown"})
            self.assertEqual(set(feature["properties"]["wind_mph"]), {None})
