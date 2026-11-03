"""
AI Agents Package
Provides the Gemini-powered conversational assistant and backend tool calling interfaces.
"""

from app.agents.agent import RestaurantOpsAgent
from app.agents.gemini_client import GeminiClientManager, GeminiConfigError
from app.agents.tool_executor import ToolExecutor
from app.agents.tools import ALL_TOOL_DECLARATIONS, GEMINI_TOOLS

__all__ = [
    "RestaurantOpsAgent",
    "GeminiClientManager",
    "GeminiConfigError",
    "ToolExecutor",
    "ALL_TOOL_DECLARATIONS",
    "GEMINI_TOOLS",
]
