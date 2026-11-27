from time import perf_counter

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


HTTP_REQUESTS_TOTAL = Counter(
    "geodashboard_http_requests_total",
    "HTTP requests handled by Geography Dashboard services.",
    ("service", "method", "route", "status_code"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "geodashboard_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("service", "method", "route"),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "geodashboard_http_requests_in_progress",
    "HTTP requests currently in progress.",
    ("service",),
)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str) -> None:
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        started_at = perf_counter()
        HTTP_REQUESTS_IN_PROGRESS.labels(self.service_name).inc()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            labels = (self.service_name, request.method, route_path)
            HTTP_REQUESTS_TOTAL.labels(*labels, str(status_code)).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(*labels).observe(perf_counter() - started_at)
            HTTP_REQUESTS_IN_PROGRESS.labels(self.service_name).dec()


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
