"""API keys for the current workspace.

Mirrors ``src/resources/api-keys.ts`` of the TypeScript SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._url import segment

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["ApiKeysResource"]


class ApiKeysResource:
    """``client.api_keys`` — everything under ``/api-keys``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def list(self) -> Any:
        """List the workspace's API keys (secrets are never returned here)."""
        return self._client.request("GET", "/api-keys/")

    def create(
        self,
        *,
        name: str,
        expires_in: int | None = None,
        remaining: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create a key. The response carries the secret, and only this once."""
        body: dict[str, Any] = {"name": name}
        if expires_in is not None:
            body["expiresIn"] = expires_in
        if remaining is not None:
            body["remaining"] = remaining
        if metadata is not None:
            body["metadata"] = metadata
        return self._client.request("POST", "/api-keys/", json=body)

    def update(
        self,
        key_id: str,
        *,
        name: str | None = None,
        enabled: bool | None = None,
        remaining: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Rename, enable/disable or re-limit a key."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if enabled is not None:
            body["enabled"] = enabled
        if remaining is not None:
            body["remaining"] = remaining
        if metadata is not None:
            body["metadata"] = metadata
        return self._client.request("PUT", f"/api-keys/{segment(key_id)}", json=body)

    def delete(self, key_id: str) -> Any:
        """Revoke a key."""
        return self._client.request("DELETE", f"/api-keys/{segment(key_id)}")
