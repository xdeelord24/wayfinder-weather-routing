from django.http import JsonResponse


class JsonErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/") and response.status_code >= 400 and not response.get("Content-Type", "").startswith("application/json"):
            return JsonResponse({"error": {"code": "request_error", "message": "The request could not be processed. Please check the input and try again."}}, status=response.status_code)
        return response
