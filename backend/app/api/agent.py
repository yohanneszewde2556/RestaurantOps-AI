"""
Agent API Router
Provides endpoints for the Gemini conversational AI assistant and configuration status checks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent import RestaurantOpsAgent
from app.agents.gemini_client import GeminiClientManager
from app.core.responses import ok
from app.database.session import get_db
from app.schemas.agent import AgentChatRequest, AgentStatusResponse

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.get(
    "/status",
    summary="Get Gemini AI integration readiness and configuration status",
)
async def get_agent_status():
    """
    Returns the readiness status of the Gemini integration without executing billable API calls:
      - is_configured: boolean indicating if a non-placeholder API key is set
      - model: the configured Gemini model name
      - message: actionable setup guidance if unconfigured
    """
    is_conf = GeminiClientManager.is_configured()
    model = GeminiClientManager.get_model_name()

    if is_conf:
        msg = f"Gemini AI Assistant is configured and ready with model '{model}'."
        status = "ready"
    else:
        msg = "Gemini API key is not configured. Insert GEMINI_API_KEY into backend/.env to activate."
        status = "unconfigured"

    payload = AgentStatusResponse(
        is_configured=is_conf,
        model=model,
        status=status,
        message=msg,
    )
    return ok(data=payload.model_dump())


@router.post(
    "/chat",
    summary="Chat with RestaurantOps AI Assistant",
)
async def chat_with_agent(
    payload: AgentChatRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Submit a user inquiry to the Gemini AI Agent:
      - Dynamically queries backend tools (inventory, sales, consumption, food costs, procurement)
      - Returns grounded conversational advice and list of tools executed
      - If unconfigured, gracefully guides the user to set their API key
    """
    history_dicts = (
        [{"role": m.role, "content": m.content} for m in payload.history]
        if payload.history
        else None
    )

    result = await RestaurantOpsAgent.chat(
        session=session,
        message=payload.message,
        conversation_id=payload.conversation_id,
        history=history_dicts,
    )
    return ok(data=result)
