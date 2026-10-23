from django.urls import path, re_path
from routing import api

urlpatterns = [
    path("api/health", api.health),
    path("api/locations", api.locations),
    path("api/plan", api.plan),
    path("api/corridor", api.corridor),
    re_path(r"^api(?:/.*)?$", api.not_found),
    re_path(r"^.*$", api.frontend),
]

handler400 = api.bad_request
handler404 = api.not_found
handler500 = api.server_error
