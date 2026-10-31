"""Workspace tags: labels to group apps and databases.

A tag is a filter: it grants no access and has no quota.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from .._url import segment

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["TagsResource"]


class TagsResource:
    """``client.tags`` — everything under ``/tags``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def list(self) -> Any:
        """The workspace's tags."""
        return self._client.request("GET", "/tags/")

    def create(self, *, name: str, color: str | None = None) -> Any:
        """Create a tag. ``name`` is 1 to 40 characters and unique in the workspace."""
        body: dict[str, Any] = {"name": name}
        if color is not None:
            body["color"] = color
        return self._client.request("POST", "/tags/", json=body)

    def update(self, tag_id: str, *, name: str | None = None, color: str | None = None) -> Any:
        """Rename or recolor a tag."""
        body = {k: v for k, v in {"name": name, "color": color}.items() if v is not None}
        return self._client.request("PATCH", f"/tags/{segment(tag_id)}", json=body)

    def delete(self, tag_id: str) -> Any:
        """Delete a tag (it disappears from every app and database)."""
        return self._client.request("DELETE", f"/tags/{segment(tag_id)}")

    def set_links(
        self, *, kind: Literal["app", "database"], id: str, tag_ids: Sequence[str]
    ) -> Any:
        """Set the tags of an app or database. ``tag_ids`` is the final list, not an addition."""
        return self._client.request(
            "PUT", "/tags/links", json={"kind": kind, "id": id, "tagIds": tag_ids}
        )
