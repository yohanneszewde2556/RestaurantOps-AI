"""
Application configuration using Pydantic Settings.
Reads all values from environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────
    APP_NAME: str = "RestaurantOps AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── API ────────────────────────────────────────────────────────
    API_PREFIX: str = "/api/v1"

    # ── CORS ───────────────────────────────────────────────────────
    # Comma-separated list of allowed origins for local dev
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Database ───────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./restaurantops.db"

    # ── AI ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    @property
    def is_gemini_configured(self) -> bool:
        key = self.GEMINI_API_KEY.strip()
        return bool(key) and key != "your_gemini_api_key_here" and not key.startswith("your_")

    # ── Telegram ───────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # ── Weather (Open-Meteo — no key required, just config) ────────
    RESTAURANT_LATITUDE: float = 40.7128   # Default: New York
    RESTAURANT_LONGITUDE: float = -74.0060

    # ── Scheduler ──────────────────────────────────────────────────
    # Cron string for the daily inventory check (default: 8 AM every day)
    INVENTORY_CHECK_CRON: str = "0 8 * * *"
    # Cron string for the daily report (default: 9 AM every day)
    DAILY_REPORT_CRON: str = "0 9 * * *"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
