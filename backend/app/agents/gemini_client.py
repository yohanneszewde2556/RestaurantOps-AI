"""
Gemini Client Wrapper
Provides connection pooling, configuration checks, and safe error handling for Google GenAI.
"""

from typing import Optional
from google import genai

from app.core.config import get_settings


class GeminiConfigError(Exception):
    """Raised when Gemini API key is missing or not configured."""
    pass


class GeminiClientManager:
    """Manages the lifecycle and configuration of the Google GenAI client."""

    _client: Optional[genai.Client] = None

    @classmethod
    def is_configured(cls) -> bool:
        """Check whether a non-empty, non-placeholder API key is set."""
        return get_settings().is_gemini_configured

    @classmethod
    def get_model_name(cls) -> str:
        """Get the configured Gemini model name, automatically upgrading legacy model identifiers."""
        model = get_settings().GEMINI_MODEL.strip()
        if not model or model.startswith("gemini-1.") or model in ("gemini-2.5-flash", "gemini-2.5-flash-lite"):
            return "gemini-3.5-flash"
        return model

    @classmethod
    def get_client(cls) -> genai.Client:
        """
        Return the initialized Google GenAI client.
        Raises GeminiConfigError if GEMINI_API_KEY is missing or invalid.
        """
        settings = get_settings()
        if not settings.is_gemini_configured:
            raise GeminiConfigError(
                "Google Gemini API key is not configured. "
                "Please add GEMINI_API_KEY to your backend .env file and restart the server."
            )

        if cls._client is None:
            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())

        return cls._client

    @classmethod
    def reset_client(cls) -> None:
        """Reset cached client instance (useful for testing or config reloads)."""
        cls._client = None
