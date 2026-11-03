"""
Standardized API response envelope.

All endpoints return one of:
  - SuccessResponse  → { "success": true,  "data": <payload>, "message": <str|null> }
  - ErrorResponse    → { "success": false, "error": <str>,    "detail": <str|null>  }

This keeps the frontend integration predictable.
"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None


def ok(data: Any, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


def err(error: str, detail: str | None = None) -> dict:
    return {"success": False, "error": error, "detail": detail}
