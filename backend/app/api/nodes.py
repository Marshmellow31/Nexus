"""Node catalogue endpoint. The frontend renders config forms from these JSON
Schemas; the AI generator plans workflows against the same list. No duplication."""

from fastapi import APIRouter

from app.modules.nodes import register_builtin_nodes
from app.modules.nodes.registry import registry

router = APIRouter(tags=["nodes"])


@router.get("/nodes")
async def list_nodes() -> dict:
    register_builtin_nodes()  # idempotent; safe if lifespan already ran
    return {"nodes": registry.all_specs()}
