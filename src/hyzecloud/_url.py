"""URL helpers shared by the client and the resources.

Kept in its own module so resources can import it without importing the client, which
would be a cycle (the client imports every resource).
"""

from __future__ import annotations

from urllib.parse import quote

__all__ = ["join_url", "segment"]


def join_url(base: str, path: str) -> str:
    """Append a path to a base URL without doubling or dropping the slash."""
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{base.rstrip('/')}{normalized_path}"


def segment(value: object) -> str:
    """Percent-encode one path segment.

    The TypeScript SDK wraps every id in ``encodeURIComponent``. Without this, an id
    containing a space, a slash or a ``?`` would silently change the route.
    """
    return quote(str(value), safe="")
