"""Apps and deployments.

Mirrors ``src/resources/apps.ts`` of the TypeScript SDK, with one deliberate difference:
Python callers use snake_case keyword arguments (``memory_mb``) and the SDK translates them
to the API's camelCase (``memoryMB``).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .._url import segment

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["AppsResource"]


def _zip_file(source: Any, filename: str) -> Any:
    """Normalize a ZIP source into what ``httpx`` needs for a multipart part.

    Accepts a path (``str``/``os.PathLike``), raw ``bytes``, or an open binary file object.
    """
    if isinstance(source, (bytes, bytearray, memoryview)):
        return (filename, bytes(source), "application/zip")
    return (filename, source, "application/zip")


class AppsResource:
    """``client.apps`` — everything under ``/apps``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def list(
        self,
        *,
        workspace_id: str | None = None,
        organization_id: str | None = None,
    ) -> Any:
        """List the apps visible to the key."""
        return self._client.request(
            "GET",
            "/apps/",
            query={"workspaceId": workspace_id, "organizationId": organization_id},
        )

    def get(self, app_id: str) -> Any:
        """Fetch one app's public detail."""
        return self._client.request("GET", f"/apps/{segment(app_id)}")

    def delete(self, app_id: str) -> Any:
        """Delete an app and its container."""
        return self._client.request("DELETE", f"/apps/{segment(app_id)}")

    def start(self, app_id: str) -> Any:
        """Start a stopped app."""
        return self._client.request("POST", f"/apps/{segment(app_id)}/start")

    def stop(self, app_id: str) -> Any:
        """Stop a running app."""
        return self._client.request("POST", f"/apps/{segment(app_id)}/stop")

    def restart(self, app_id: str) -> Any:
        """Restart an app."""
        return self._client.request("POST", f"/apps/{segment(app_id)}/restart")

    def logs(
        self,
        app_id: str,
        *,
        tail: int | None = None,
        timestamps: bool | None = None,
        since: str | int | None = None,
        until: str | int | None = None,
    ) -> Any:
        """Read container logs."""
        return self._client.request(
            "GET",
            f"/apps/{segment(app_id)}/logs",
            query={"tail": tail, "timestamps": timestamps, "since": since, "until": until},
        )

    def deployments(self, app_id: str, *, page: int | None = None, limit: int | None = None) -> Any:
        """Paged deploy history (``/deployments``)."""
        return self._client.request(
            "GET", f"/apps/{segment(app_id)}/deployments", query={"page": page, "limit": limit}
        )

    def get_env(self, app_id: str) -> Any:
        """Read the app's environment variables."""
        return self._client.request("GET", f"/apps/{segment(app_id)}/env")

    def set_env(self, app_id: str, env_vars: dict[str, str]) -> Any:
        """Replace the app's environment variables."""
        return self._client.request(
            "PUT", f"/apps/{segment(app_id)}/env", json={"envVars": env_vars}
        )

    def update_settings(
        self,
        app_id: str,
        *,
        name: str | None = None,
        runtime: str | None = None,
        memory_mb: int | None = None,
        startup_command: str | None = None,
        expose_port: int | None = None,
        subdomain: str | None = None,
        auto_restart: bool | None = None,
    ) -> Any:
        """Update app settings. Only the arguments you pass are sent."""
        settings: dict[str, Any] = {}
        if name is not None:
            settings["name"] = name
        if runtime is not None:
            settings["runtime"] = runtime
        if memory_mb is not None:
            settings["memoryMB"] = memory_mb
        if startup_command is not None:
            settings["startupCommand"] = startup_command
        if expose_port is not None:
            settings["exposePort"] = expose_port
        if subdomain is not None:
            settings["subdomain"] = subdomain
        if auto_restart is not None:
            settings["autoRestart"] = auto_restart
        return self._client.request("PUT", f"/apps/{segment(app_id)}/settings", json=settings)

    def deploy_from_zip(
        self,
        *,
        file: Any,
        name: str,
        runtime: str,
        memory_mb: int,
        filename: str = "app.zip",
        startup_command: str | None = None,
        env_vars: dict[str, str] | str | None = None,
        expose_port: int | None = None,
        subdomain: str | None = None,
        auto_restart: bool | None = None,
        machine_id: str | None = None,
        workspace_id: str | None = None,
    ) -> Any:
        """Deploy from a ZIP (multipart upload).

        Args:
            file: A path, raw ``bytes``, or an open binary file object.
            startup_command: Omit or pass ``"auto"`` to let Hyze detect the start command.
        """
        data: dict[str, str] = {
            "name": name,
            "runtime": runtime,
            "memoryMB": str(memory_mb),
            "startupCommand": startup_command.strip() if startup_command else "auto",
        }
        if env_vars is not None:
            data["envVars"] = env_vars if isinstance(env_vars, str) else json.dumps(env_vars)
        if expose_port is not None:
            data["exposePort"] = str(expose_port)
        if subdomain is not None:
            data["subdomain"] = subdomain
        if auto_restart is not None:
            data["autoRestart"] = "true" if auto_restart else "false"
        if machine_id is not None:
            data["machineId"] = machine_id
        if workspace_id is not None:
            data["workspaceId"] = workspace_id

        return self._client.request(
            "POST",
            "/apps/deploy",
            files={"file": _zip_file(file, filename)},
            data=data,
        )

    def deploy_from_repo(
        self,
        *,
        name: str,
        runtime: str,
        memory_mb: int,
        repository: dict[str, Any],
        startup_command: str | None = None,
        env_vars: dict[str, str] | str | None = None,
        expose_port: int | None = None,
        subdomain: str | None = None,
        auto_deploy: bool | None = None,
        machine_id: str | None = None,
        workspace_id: str | None = None,
    ) -> Any:
        """Deploy from a connected GitHub repository."""
        body: dict[str, Any] = {
            "name": name,
            "runtime": runtime,
            "memoryMB": memory_mb,
            "repository": repository,
        }
        if startup_command is not None:
            body["startupCommand"] = startup_command
        if env_vars is not None:
            body["envVars"] = env_vars
        if expose_port is not None:
            body["exposePort"] = expose_port
        if subdomain is not None:
            body["subdomain"] = subdomain
        if auto_deploy is not None:
            body["autoDeploy"] = auto_deploy
        if machine_id is not None:
            body["machineId"] = machine_id
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        return self._client.request("POST", "/apps/deploy-from-repo", json=body)

    def inspect_env(self, file: Any, filename: str = "app.zip") -> Any:
        """Detect the environment variables of a ZIP without deploying it."""
        return self._client.request(
            "POST", "/apps/inspect-env", files={"file": _zip_file(file, filename)}
        )

    def create_backup(self, app_id: str) -> Any:
        """Back up the app now."""
        return self._client.request("POST", f"/apps/{segment(app_id)}/backup")

    def list_backups(self, app_id: str) -> Any:
        """List the app's backups."""
        return self._client.request("GET", f"/apps/{segment(app_id)}/backups")

    def delete_backups(self, app_id: str) -> Any:
        """Delete every backup of the app."""
        return self._client.request("DELETE", f"/apps/{segment(app_id)}/backups")

    def restore_backup(self, app_id: str, backup_id: str) -> Any:
        """Restore the app from a backup."""
        return self._client.request(
            "POST", f"/apps/{segment(app_id)}/backups/restore", json={"backupId": backup_id}
        )

    def download_backup(self, app_id: str, backup_id: str) -> Any:
        """Download a backup archive."""
        return self._client.request(
            "GET", f"/apps/{segment(app_id)}/backups/{segment(backup_id)}/download"
        )
