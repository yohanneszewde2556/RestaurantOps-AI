"""
Agent Orchestrator for RestaurantOps AI
Coordinates conversational interaction, tool execution loop, and safe error handling with Gemini.
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.gemini_client import GeminiClientManager, GeminiConfigError
from app.agents.prompts import RESTAURANTOPS_AGENT_SYSTEM_PROMPT
from app.agents.tool_executor import ToolExecutor
from app.agents.tools import GEMINI_TOOLS

logger = logging.getLogger("restaurantops.agent")


class ToolCallRecord:
    def __init__(self, name: str, args: Dict[str, Any], result: Dict[str, Any]):
        self.name = name
        self.args = args
        self.result = result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.name,
            "arguments": self.args,
            "result_summary": {
                k: v for k, v in self.result.items() if not isinstance(v, list) or len(v) <= 3
            },
        }


class RestaurantOpsAgent:
    """Orchestrates conversations with Google Gemini and manages tool calling against backend services."""

    MAX_TOOL_TURNS = 5

    @classmethod
    async def chat(
        cls,
        session: AsyncSession,
        message: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message through Gemini with tool-assisted service execution.
        """
        conv_id = conversation_id or str(uuid.uuid4())

        # 1. Check if Gemini API key is configured
        if not GeminiClientManager.is_configured():
            return {
                "conversation_id": conv_id,
                "response": (
                    "### ⚠️ Google Gemini API Key Not Configured\n\n"
                    "The AI Assistant requires a valid Google Gemini API key to query your restaurant database and assist with operations.\n\n"
                    "**How to configure:**\n"
                    "1. Open your backend environment file:\n"
                    "   `backend/.env`\n"
                    "2. Locate line 23: `GEMINI_API_KEY=`\n"
                    "3. Paste your Gemini API key obtained from [Google AI Studio](https://aistudio.google.com/app/apikey).\n"
                    "4. Restart the FastAPI backend server.\n\n"
                    "Once added, I will immediately be able to analyze your pantry stock, track consumption, and draft procurement orders."
                ),
                "tools_called": [],
                "is_configured": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            client = GeminiClientManager.get_client()
            model_name = GeminiClientManager.get_model_name()
        except GeminiConfigError as e:
            return {
                "conversation_id": conv_id,
                "response": f"Configuration Error: {str(e)}",
                "tools_called": [],
                "is_configured": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # 2. Build conversation contents
        contents: List[Any] = []
        if history:
            for msg in history[-8:]:  # Include last 8 messages for context
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.get("content", ""))],
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
        )

        tools_called_records: List[ToolCallRecord] = []
        config = types.GenerateContentConfig(
            system_instruction=RESTAURANTOPS_AGENT_SYSTEM_PROMPT,
            tools=GEMINI_TOOLS,
            temperature=0.2,  # Low temperature for factual, deterministic consistency
        )

        # 3. Multi-turn execution loop for tool calls
        try:
            for _ in range(cls.MAX_TOOL_TURNS):
                # Call Gemini API
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model_name,
                    contents=contents,
                    config=config,
                )

                # Check if Gemini requested function calls
                if not response.function_calls:
                    # Final text response received
                    final_text = response.text or "I have processed your request based on your current operational data."
                    return {
                        "conversation_id": conv_id,
                        "response": final_text,
                        "tools_called": [t.to_dict() for t in tools_called_records],
                        "is_configured": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                # Gemini requested one or more tool executions
                # Append the model's tool call turn to contents
                if response.candidates and response.candidates[0].content:
                    contents.append(response.candidates[0].content)

                tool_response_parts: List[types.Part] = []

                for call in response.function_calls:
                    call_name = call.name
                    call_args = call.args or {}
                    logger.info("Agent executing tool: %s with args: %s", call_name, call_args)

                    try:
                        tool_result = await ToolExecutor.execute(session, call_name, call_args)
                    except Exception as err:
                        logger.error("Error executing tool %s: %s", call_name, err)
                        tool_result = {"error": f"Tool execution failed: {str(err)}"}

                    tools_called_records.append(ToolCallRecord(call_name, call_args, tool_result))

                    # Format part to return tool result back to Gemini
                    part = types.Part.from_function_response(
                        name=call_name,
                        response=tool_result,
                    )
                    tool_response_parts.append(part)

                # Append function responses as user turn
                contents.append(types.Content(role="user", parts=tool_response_parts))

            # Exceeded tool turn limit fallback
            return {
                "conversation_id": conv_id,
                "response": "I evaluated multiple operational tools but reached the turn limit. Please review the tool activity above.",
                "tools_called": [t.to_dict() for t in tools_called_records],
                "is_configured": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except APIError as api_err:
            logger.error("Gemini API Error: %s", api_err)
            error_msg = str(api_err)
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                user_msg = "⚠️ Gemini API rate limit or quota exceeded. Please wait a moment before sending another message."
            else:
                user_msg = f"⚠️ Gemini service error: {api_err.message if hasattr(api_err, 'message') else 'Request failed.'}"

            return {
                "conversation_id": conv_id,
                "response": user_msg,
                "tools_called": [t.to_dict() for t in tools_called_records],
                "is_configured": True,
                "error": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.exception("Unexpected error in agent interaction: %s", exc)
            return {
                "conversation_id": conv_id,
                "response": "⚠️ An unexpected error occurred while communicating with the AI service. Please try again.",
                "tools_called": [t.to_dict() for t in tools_called_records],
                "is_configured": True,
                "error": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
