"""Plans and usage.

Mirrors ``src/resources/plans.ts`` of the TypeScript SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["PlansResource"]


class PlansResource:
    """``client.plans`` — everything under ``/plans``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def current(self) -> Any:
        """Current plan plus usage summary (no nested apps/databases lists)."""
        return self._client.request("GET", "/plans/current")

    def list(self) -> Any:
        """Every plan available for purchase."""
        return self._client.request("GET", "/plans/")
