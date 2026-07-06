"""FastAPI application factory.

Same codebase powers two processes: this API and the arq worker. The API never
executes workflows — it enqueues them.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.modules.nodes import register_builtin_nodes


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_builtin_nodes()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        version="0.1.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    from app.api.ai import router as ai_router
    from app.api.integrations import router as integrations_router
    from app.api.auth import router as auth_router
    from app.api.health import router as health_router
    from app.api.nodes import router as nodes_router
    from app.api.runs import router as runs_router
    from app.api.workflows import router as workflows_router

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(nodes_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(workflows_router, prefix=settings.api_prefix)
    app.include_router(runs_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(integrations_router, prefix=settings.api_prefix)

    return app


app = create_app()
