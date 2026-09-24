"""GitHub integration.

Mirrors ``src/resources/github.ts`` of the TypeScript SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._url import segment

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["GithubResource"]


class GithubResource:
    """``client.github`` — everything under ``/integrations/github``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def status(self) -> Any:
        """Whether the workspace has a GitHub App installation and the scopes it holds."""
        return self._client.request("GET", "/integrations/github/status")

    def install_url(self) -> Any:
        """The URL to send a user to in order to install the GitHub App."""
        return self._client.request("GET", "/integrations/github/install-url")

    def disconnect(self) -> Any:
        """Drop the stored GitHub connection."""
        return self._client.request("DELETE", "/integrations/github/connection")

    def repos(self) -> Any:
        """List the repositories the installation can see."""
        return self._client.request("GET", "/integrations/github/repos")

    def branches(self, owner: str, repo: str) -> Any:
        """List the branches of one repository."""
        return self._client.request(
            "GET",
            f"/integrations/github/repos/{segment(owner)}/{segment(repo)}/branches",
        )

    def detect_runtime(
        self, owner: str, repo: str, *, branch: str | None = None, path: str | None = None
    ) -> Any:
        """Detect the runtime of a repository without deploying it."""
        return self._client.request(
            "GET",
            f"/integrations/github/repos/{segment(owner)}/{segment(repo)}/runtime",
            query={"branch": branch, "path": path},
        )
