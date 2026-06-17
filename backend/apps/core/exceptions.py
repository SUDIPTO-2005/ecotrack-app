"""Custom DRF exception handler for EcoTrack."""
from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    """Custom exception handler that returns consistent JSON error responses.

    Wraps DRF's default handler to add structured error codes and
    ensures all error responses have a consistent shape::

        {
            "error": {
                "code": "not_found",
                "message": "Resource not found.",
                "details": {}
            }
        }

    Args:
        exc: The exception that was raised.
        context: DRF context dict containing the view and request.

    Returns:
        A DRF Response with standardised error body, or None to let
        Django's default error handling take over.
    """
    # Let DRF handle it first
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exceptions — log and return 500
        if isinstance(exc, Exception):
            logger.exception("Unhandled exception in view", exc_info=exc)
        return None

    # Normalise the response shape
    error_code = "error"
    if isinstance(exc, Http404):
        error_code = "not_found"
    elif isinstance(exc, PermissionDenied):
        error_code = "permission_denied"
    elif isinstance(exc, APIException):
        error_code = exc.default_code if hasattr(exc, "default_code") else "api_error"

    response.data = {
        "error": {
            "code": error_code,
            "message": _extract_message(response.data),
            "details": response.data if isinstance(response.data, dict) else {},
            "status": response.status_code,
        }
    }
    return response


def _extract_message(data: Any) -> str:
    """Extract a human-readable message from DRF error data.

    Args:
        data: The raw error data from a DRF response.

    Returns:
        A single human-readable string summarising the error.
    """
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        if "non_field_errors" in data:
            errors = data["non_field_errors"]
            return str(errors[0]) if errors else "Validation error."
        return "Validation error. See details."
    if isinstance(data, list):
        return str(data[0]) if data else "An error occurred."
    return str(data)
