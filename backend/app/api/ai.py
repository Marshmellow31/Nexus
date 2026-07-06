"""AI workflow generation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.ai.generator import WorkflowGenerator
from app.modules.ai.service import AIService, LiteLLMProvider
from app.modules.auth.dependencies import get_current_user
from app.core.config import settings
from app.modules.auth.models import User
from app.modules.nodes import register_builtin_nodes
from app.modules.nodes.registry import registry

router = APIRouter(prefix="/ai", tags=["ai"])


class GenerateWorkflowRequest(BaseModel):
    description: str
    api_key: str | None = None  # user's Gemini API key; falls back to system key


class GenerateWorkflowResponse(BaseModel):
    name: str
    description: str | None
    definition: dict


@router.post("/generate-workflow", response_model=GenerateWorkflowResponse)
async def generate_workflow(
    body: GenerateWorkflowRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    register_builtin_nodes()
    ai = AIService(LiteLLMProvider())
    generator = WorkflowGenerator(ai, registry)
    # Use user's key if provided, else fall back to system Gemini key from env
    api_key = body.api_key or (settings.gemini_api_key or None)
    result = await generator.generate(body.description, api_key=api_key)
    return GenerateWorkflowResponse(
        name=result.get("name", "Generated workflow"),
        description=result.get("description"),
        definition={"nodes": result.get("nodes", []), "edges": result.get("edges", [])},
    )
