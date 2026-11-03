"""
Automated Tests for Gemini AI Agent, Tools, and Chat API.
All tests run hermetically without requiring an external Gemini API key.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.gemini_client import GeminiClientManager, GeminiConfigError
from app.agents.tool_executor import ToolExecutor
from app.core.config import get_settings
from app.core.exceptions import ValidationException
from app.models.ingredient import Ingredient
from app.models.procurement import ProcurementRecommendation, RecommendationStatus
from app.services.procurement_service import ProcurementService


# ─────────────────────────────────────────────────────────────────────
# 1. STATUS & CONFIGURATION TESTS
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_status_endpoint_unconfigured(client: AsyncClient):
    """When API key is empty or placeholder, /agent/status returns unconfigured."""
    with patch("app.core.config.Settings.is_gemini_configured", False):
        resp = await client.get("/api/v1/agent/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["is_configured"] is False
        assert body["data"]["status"] == "unconfigured"
        assert "not configured" in body["data"]["message"]


@pytest.mark.asyncio
async def test_agent_status_endpoint_configured(client: AsyncClient):
    """When API key is valid, /agent/status returns ready."""
    with patch("app.core.config.Settings.is_gemini_configured", True):
        resp = await client.get("/api/v1/agent/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["is_configured"] is True
        assert body["data"]["status"] == "ready"


@pytest.mark.asyncio
async def test_agent_chat_unconfigured_guidance(client: AsyncClient):
    """When API key is missing, /agent/chat returns a helpful setup guide instead of 500 error."""
    with patch("app.core.config.Settings.is_gemini_configured", False):
        payload = {"message": "What ingredients are running low?"}
        resp = await client.post("/api/v1/agent/chat", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["is_configured"] is False
        assert "Google Gemini API Key Not Configured" in data["response"]
        assert "GEMINI_API_KEY=" in data["response"]
        assert data["tools_called"] == []


# ─────────────────────────────────────────────────────────────────────
# 2. TOOL EXECUTOR UNIT TESTS (ALL 8 TOOLS)
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tool_get_inventory(db_session: AsyncSession):
    """Verify Tool 1: get_inventory retrieves ingredient records."""
    ing = Ingredient(
        name="Organic Basil",
        sku="ING-HERB-BASIL",
        category="Produce",
        unit="kg",
        current_quantity=Decimal("5.000"),
        min_quantity=Decimal("1.000"),
        cost_per_unit=Decimal("15.00"),
    )
    db_session.add(ing)
    await db_session.commit()

    res = await ToolExecutor.execute(db_session, "get_inventory", {"category": "Produce"})
    assert res["total_ingredients_in_catalog"] >= 1
    found = any(i["sku"] == "ING-HERB-BASIL" for i in res["ingredients"])
    assert found is True


@pytest.mark.asyncio
async def test_tool_get_low_stock_and_expiring(db_session: AsyncSession):
    """Verify Tool 3 (get_low_stock_ingredients) and Tool 4 (get_expiring_ingredients)."""
    now = datetime.now(timezone.utc)
    today = now.date()

    ing_low = Ingredient(
        name="Low Butter",
        sku="ING-BUTTER-LOW",
        category="Dairy",
        unit="kg",
        current_quantity=Decimal("1.000"),
        min_quantity=Decimal("5.000"), # below min!
        cost_per_unit=Decimal("8.00"),
        expiry_date=today + timedelta(days=3), # expiring in 3 days!
    )
    db_session.add(ing_low)
    await db_session.commit()

    # Tool 3: low stock
    low_res = await ToolExecutor.execute(db_session, "get_low_stock_ingredients", {})
    assert low_res["low_stock_count"] >= 1
    low_item = next(i for i in low_res["items"] if i["sku"] == "ING-BUTTER-LOW")
    assert low_item["deficit"] == 4.0

    # Tool 4: expiring
    exp_res = await ToolExecutor.execute(db_session, "get_expiring_ingredients", {"days": 7})
    assert exp_res["expiring_count"] >= 1
    exp_item = next(i for i in exp_res["items"] if i["sku"] == "ING-BUTTER-LOW")
    assert exp_item["days_remaining"] == 3


@pytest.mark.asyncio
async def test_tool_analyze_stock_levels(db_session: AsyncSession):
    """Verify Tool 5: analyze_stock_levels synthesizes low-stock and burn rates."""
    res = await ToolExecutor.execute(db_session, "analyze_stock_levels", {"days": 30})
    assert "total_low_stock_items" in res
    assert "items_analyzed" in res
    assert "top_consumed_pantry_items" in res


@pytest.mark.asyncio
async def test_tool_generate_purchase_plan_creates_pending_only(db_session: AsyncSession):
    """
    Verify Tool 6: generate_purchase_plan generates recommendations strictly with PENDING status.
    AI must never approve or execute purchases.
    """
    res = await ToolExecutor.execute(db_session, "generate_purchase_plan", {"reason": "Test restock"})
    assert res["status"] == RecommendationStatus.PENDING.value
    assert "PENDING" in res["governance_note"]
    assert "explicitly approve" in res["governance_note"]
    assert "recommendation_id" in res

    # Verify recommendation in database is actually PENDING
    rec_id = res["recommendation_id"]
    rec = await ProcurementService.get_by_id(db_session, rec_id)
    assert rec.status == RecommendationStatus.PENDING.value

    # AI is prohibited from approving it
    with pytest.raises(ValidationException):
        await ToolExecutor.execute(db_session, "approve_procurement", {"recommendation_id": rec_id})


@pytest.mark.asyncio
async def test_tool_consumption_and_food_cost_analytics(db_session: AsyncSession):
    """Verify Tool 7 (consumption) and Tool 8 (food cost) execution."""
    c_res = await ToolExecutor.execute(db_session, "get_consumption_analytics", {"limit": 5})
    assert "period_summary" in c_res
    assert "top_consumed_ingredients" in c_res

    fc_res = await ToolExecutor.execute(db_session, "get_food_cost_analytics", {})
    assert "total_menu_items" in fc_res
    assert "overall_tier" in fc_res


@pytest.mark.asyncio
async def test_tool_unauthorized_name_rejected(db_session: AsyncSession):
    """Verify ToolExecutor strictly rejects unknown or unauthorized tool calls."""
    with pytest.raises(ValidationException) as exc_info:
        await ToolExecutor.execute(db_session, "delete_database", {})
    assert "Unauthorized or unknown tool" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────────────
# 3. MOCKED GEMINI AGENT CONVERSATION TESTS
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_chat_with_mocked_gemini(client: AsyncClient):
    """
    Simulate a Gemini conversation turn where the model calls a tool and returns an answer.
    Tests the full agent loop without external API dependency.
    """
    # Mock Gemini response objects
    mock_func_call = MagicMock()
    mock_func_call.name = "get_low_stock_ingredients"
    mock_func_call.args = {}

    # Turn 1: Model requests tool call
    mock_turn1 = MagicMock()
    mock_turn1.function_calls = [mock_func_call]
    mock_turn1.candidates = [MagicMock(content=MagicMock())]

    # Turn 2: Model gives final text response
    mock_turn2 = MagicMock()
    mock_turn2.function_calls = None
    mock_turn2.text = "You currently have 1 low stock ingredient: Low Butter (1.0 kg remaining)."

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [mock_turn1, mock_turn2]

    with patch("app.agents.gemini_client.GeminiClientManager.is_configured", return_value=True), \
         patch("app.agents.gemini_client.GeminiClientManager.get_client", return_value=mock_client), \
         patch("app.agents.gemini_client.GeminiClientManager.get_model_name", return_value="gemini-2.5-flash"):

        payload = {"message": "Which ingredients are low in stock?"}
        resp = await client.post("/api/v1/agent/chat", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert "Low Butter" in data["response"]
        assert len(data["tools_called"]) == 1
        assert data["tools_called"][0]["tool_name"] == "get_low_stock_ingredients"


@pytest.mark.asyncio
async def test_agent_chat_validation_error(client: AsyncClient):
    """Verify validation error when sending empty message."""
    resp = await client.post("/api/v1/agent/chat", json={"message": ""})
    assert resp.status_code == 422
