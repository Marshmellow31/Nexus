"""Domain error types + FastAPI exception handlers.

Keep HTTP concerns out of the domain: raise these anywhere, translate at the edge.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


class NexusError(Exception):
    """Base for all expected/handled application errors."""

    status_code = 400
    code = "nexus_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(NexusError):
    status_code = 404
    code = "not_found"


class AuthError(NexusError):
    status_code = 401
    code = "unauthorized"


class PermissionError(NexusError):
    status_code = 403
    code = "forbidden"


class ValidationError(NexusError):
    status_code = 422
    code = "validation_error"


class ConflictError(NexusError):
    status_code = 409
    code = "conflict"


class RateLimitError(NexusError):
    status_code = 429
    code = "rate_limited"


def register_exception_handlers(app: "FastAPI") -> None:
    from fastapi import Request
    from fastapi.responses import ORJSONResponse

    @app.exception_handler(NexusError)
    async def _handle_nexus_error(_: Request, exc: NexusError) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
