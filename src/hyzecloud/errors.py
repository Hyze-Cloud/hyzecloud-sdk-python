"""Errors raised by the Hyze Cloud SDK.

Mirrors ``src/errors.ts`` of the TypeScript SDK (``@hyze-cloud/sdk``) so the two clients
behave the same way for the same API response.
"""

from __future__ import annotations

from typing import Any

__all__ = ["HyzeError", "looks_like_error_payload", "parse_error_body"]


class HyzeError(Exception):
    """A non-2xx response, or a 2xx body that is shaped like an error.

    Attributes:
        message: Human-readable message extracted from the payload.
        status: HTTP status code (401 when a 2xx body looked like an error).
        code: Structured error code from the payload, when the API sent one.
        body: The decoded payload, untouched.
        retry_after_seconds: Value of the ``Retry-After`` header, when present and non-zero.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str | None = None,
        body: Any = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.body = body
        self.retry_after_seconds = retry_after_seconds

    @property
    def is_rate_limited(self) -> bool:
        """True when the API answered 429."""
        return self.status == 429

    @property
    def is_unauthorized(self) -> bool:
        """True when the API answered 401 or 403."""
        return self.status in (401, 403)

    @property
    def is_not_found(self) -> bool:
        """True when the API answered 404."""
        return self.status == 404

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(status={self.status!r}, code={self.code!r}, "
            f"message={self.message!r})"
        )


def parse_error_body(body: Any) -> tuple[str, str | None]:
    """Pull a message and a code out of whatever shape the API answered with.

    Returns:
        A ``(message, code)`` pair. ``code`` is ``None`` when the payload carried none.
    """
    if isinstance(body, str):
        trimmed = body.strip()
        return (trimmed or "Request failed", None)

    if not isinstance(body, dict):
        return ("Request failed", None)

    error = body.get("error")
    code = body.get("code")
    code = code if isinstance(code, str) else None

    if isinstance(error, str):
        return (error, code)

    if isinstance(error, dict):
        message = error.get("message") or body.get("message")
        error_code = error.get("code") or code
        return (
            message if isinstance(message, str) else "Request failed",
            error_code if isinstance(error_code, str) else None,
        )

    message = body.get("message")
    if isinstance(message, str):
        return (message, code)

    return ("Request failed", code)


def looks_like_error_payload(body: Any) -> bool:
    """Detect an error-shaped payload even when the HTTP status is wrongly 2xx."""
    if isinstance(body, str):
        text = body.strip().lower()
        return (
            text in ("unauthorized", "forbidden", "not found")
            or text.startswith("error")
            or "unauthorized" in text
        )

    if not isinstance(body, dict):
        return False

    if body.get("success") is False:
        return True

    error = body.get("error")
    if isinstance(error, str) and error:
        return True

    return isinstance(error, dict)
