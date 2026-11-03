"""
Custom Application Exceptions.

Handled globally by FastAPI exception handlers to produce consistent
{ "success": false, "error": ..., "detail": ... } responses.
"""

from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        detail: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            detail=f"{resource} with identifier '{identifier}' does not exist.",
        )


class ConflictException(AppException):
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=409,
            detail=detail,
        )


class ValidationException(AppException):
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            detail=detail,
        )


class InsufficientStockException(AppException):
    def __init__(self, details: list[dict[str, Any]]):
        super().__init__(
            message="Insufficient inventory stock for requested operation",
            status_code=400,
            detail=details,
        )
