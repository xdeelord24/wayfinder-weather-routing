from datetime import datetime, timedelta, timezone
from math import isfinite

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework import serializers
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import exception_handler as drf_exception_handler

from . import demo, providers, services
from .domain import haversine
from .errors import ServiceError


def error_response(code, message, status):
    return Response({"error": {"code": code, "message": message}}, status=status)


def _error_text(detail):
    if isinstance(detail, dict):
        return "; ".join(f"{key}: {_error_text(value)}" for key, value in detail.items())
    if isinstance(detail, (tuple, list)):
        return "; ".join(_error_text(item) for item in detail)
    return str(detail)


def exception_handler(exc, context):
    if isinstance(exc, ServiceError):
        return error_response(exc.code, exc.message, exc.status)
    response = drf_exception_handler(exc, context)
    if response is not None:
        code = "invalid_request" if response.status_code == 400 else "rate_limited" if response.status_code == 429 else "request_error"
        response.data = {"error": {"code": code, "message": _error_text(response.data)}}
        return response
    return error_response("internal_error", "The server could not complete the request. Please retry.", 500)


class LocationThrottle(AnonRateThrottle):
    scope = "locations"


class PlanThrottle(AnonRateThrottle):
    scope = "plan"


class CorridorThrottle(AnonRateThrottle):
    scope = "corridor"


class LocationSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=512)
    label = serializers.CharField(max_length=240)
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    timezone = serializers.CharField(max_length=100)

    def validate(self, attrs):
        if not all(isfinite(attrs[key]) for key in ("lat", "lon")):
            raise serializers.ValidationError("Coordinates must be finite numbers.")
        return attrs


class PlanSerializer(serializers.Serializer):
    origin = LocationSerializer()
    destination = LocationSerializer()
    departure = serializers.CharField(max_length=64)
    load_lbs = serializers.FloatField(min_value=0)
    spacing_miles = serializers.ChoiceField(choices=(10, 25, 50))
    mode = serializers.ChoiceField(choices=("demo", "live"))
    scenario = serializers.ChoiceField(choices=("mixed", "blocked", "clear"), default="mixed")

    def validate_departure(self, value):
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if moment.tzinfo is None or moment.utcoffset() is None:
                raise ValueError
            moment = moment.astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            raise serializers.ValidationError("Use an ISO date and time with an explicit UTC offset.") from None
        now = datetime.now(timezone.utc)
        if moment < now - timedelta(minutes=1) or moment > now + timedelta(hours=48):
            raise serializers.ValidationError("Choose a departure from now through the next 48 hours. The current minute is accepted.")
        return moment

    def validate_load_lbs(self, value):
        if not isfinite(value):
            raise serializers.ValidationError("Load must be a finite number.")
        return value

    def validate(self, attrs):
        if haversine([attrs["origin"]["lon"], attrs["origin"]["lat"]], [attrs["destination"]["lon"], attrs["destination"]["lat"]]) < 100:
            raise serializers.ValidationError("Choose an origin and destination at least 100 meters apart.")
        return attrs


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "routing_configured": bool(settings.TOMTOM_API_KEY)})


@api_view(["GET"])
@throttle_classes([LocationThrottle])
def locations(request):
    query = request.query_params.get("q", "").strip()
    mode = request.query_params.get("mode", "live")
    if mode not in ("live", "demo"):
        raise ServiceError("invalid_mode", "Choose live or demo mode.", 400)
    if len(query) > 200:
        raise ServiceError("invalid_query", "Location search is limited to 200 characters.", 400)
    if len(query) < 2:
        return Response({"locations": []})
    result = demo.locations(query) if mode == "demo" else providers.search_locations(query)
    return Response({"locations": result})


@api_view(["POST"])
@throttle_classes([PlanThrottle])
def plan(request):
    serializer = PlanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(services.create_plan(serializer.validated_data))


@api_view(["POST"])
@throttle_classes([CorridorThrottle])
def corridor(request):
    # Explicit shape validation keeps unhashable/oversized cache keys out.
    if not isinstance(request.data, dict):
        raise ServiceError("invalid_request", "Provide a JSON object containing plan_id.", 400)
    plan_id = request.data.get("plan_id")
    if not isinstance(plan_id, str) or not 1 <= len(plan_id) <= 64:
        raise ServiceError("invalid_request", "Provide the plan_id returned by route calculation.", 400)
    return Response(services.create_corridor(plan_id))


def frontend(request):
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        return JsonResponse({"error": {"code": "frontend_not_built", "message": "The API is ready. Build frontend/dist or start the Vite development server to open the app."}}, status=503)
    return HttpResponse(index.read_bytes(), content_type="text/html")


def not_found(request, exception=None):
    return JsonResponse({"error": {"code": "not_found", "message": "This API endpoint does not exist."}}, status=404)


def bad_request(request, exception=None):
    return JsonResponse({"error": {"code": "invalid_request", "message": "The request could not be processed."}}, status=400)


def server_error(request):
    return JsonResponse({"error": {"code": "internal_error", "message": "The server could not complete the request. Please retry."}}, status=500)
