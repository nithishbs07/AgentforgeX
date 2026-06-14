import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.monitoring.metrics_registry import metrics_registry

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            latency_ms = (time.time() - start_time) * 1000.0
            # Track only HTTP requests (exclude websocket if any)
            if request.scope.get("type") == "http":
                metrics_registry.increment_request(latency_ms, status_code)
                
        return response
