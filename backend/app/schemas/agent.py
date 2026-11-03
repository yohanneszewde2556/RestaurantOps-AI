"""
Pydantic Schemas: AI Agent
Request and response models for conversational AI assistant and tool execution logs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessageInput(BaseModel):
    role: str = Field(description="Message author role: 'user' or 'assistant' / 'model'")
    content: str = Field(description="Message body text")


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="User prompt or question")
    conversation_id: Optional[str] = Field(None, description="Client session or conversation tracking ID")
    history: Optional[List[ChatMessageInput]] = Field(default=None, description="Previous conversation turns")


class ToolExecutionMeta(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result_summary: Dict[str, Any]


class AgentChatResponse(BaseModel):
    conversation_id: str
    response: str
    tools_called: List[ToolExecutionMeta] = Field(default_factory=list)
    is_configured: bool
    timestamp: str


class AgentStatusResponse(BaseModel):
    is_configured: bool
    model: str
    provider: str = "Google Gemini (google-genai)"
    status: str
    message: str
