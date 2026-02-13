"""API middleware — authentication and security."""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {"/api/v1/health", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header on all non-public endpoints."""

    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        provided = request.headers.get("X-API-Key")
        if not provided or provided != self.api_key:
            client_host = request.client.host if request.client else "unknown"
            logger.warning("Unauthorized request to %s from %s", request.url.path, client_host)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
