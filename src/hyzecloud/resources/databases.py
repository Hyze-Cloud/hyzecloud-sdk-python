"""Managed databases.

Mirrors ``src/resources/databases.ts`` of the TypeScript SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._url import segment

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["DatabasesResource"]


class DatabasesResource:
    """``client.databases`` — everything under ``/databases``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def list(self, *, workspace_id: str | None = None) -> Any:
        """List the databases visible to the key."""
        return self._client.request("GET", "/databases/", query={"workspaceId": workspace_id})

    def get(self, database_id: str) -> Any:
        """Fetch one database's public row."""
        return self._client.request("GET", f"/databases/{segment(database_id)}")

    def create(
        self,
        *,
        name: str,
        engine: str,
        version: str | None = None,
        memory_mb: int | None = None,
        storage_gb: float | None = None,
        username: str | None = None,
        password: str | None = None,
        database_name: str | None = None,
        machine_id: str | None = None,
        workspace_id: str | None = None,
    ) -> Any:
        """Provision a new database."""
        body: dict[str, Any] = {"name": name, "engine": engine}
        if version is not None:
            body["version"] = version
        if memory_mb is not None:
            body["memoryMB"] = memory_mb
        if storage_gb is not None:
            body["storageGB"] = storage_gb
        if username is not None:
            body["username"] = username
        if password is not None:
            body["password"] = password
        if database_name is not None:
            body["databaseName"] = database_name
        if machine_id is not None:
            body["machineId"] = machine_id
        if workspace_id is not None:
            body["workspaceId"] = workspace_id
        return self._client.request("POST", "/databases/", json=body)

    def delete(self, database_id: str) -> Any:
        """Delete a database and its volume."""
        return self._client.request("DELETE", f"/databases/{segment(database_id)}")

    def update_settings(
        self,
        database_id: str,
        *,
        name: str | None = None,
        memory_mb: int | None = None,
        storage_gb: float | None = None,
    ) -> Any:
        """Update database settings. Only the arguments you pass are sent."""
        settings: dict[str, Any] = {}
        if name is not None:
            settings["name"] = name
        if memory_mb is not None:
            settings["memoryMB"] = memory_mb
        if storage_gb is not None:
            settings["storageGB"] = storage_gb
        return self._client.request(
            "PATCH", f"/databases/{segment(database_id)}/settings", json=settings
        )

    def stats(self, database_id: str) -> Any:
        """CPU / memory / connection stats."""
        return self._client.request("GET", f"/databases/{segment(database_id)}/stats")

    def logs(
        self, database_id: str, *, tail: int | None = None, timestamps: bool | None = None
    ) -> Any:
        """Read database logs."""
        return self._client.request(
            "GET",
            f"/databases/{segment(database_id)}/logs",
            query={"tail": tail, "timestamps": timestamps},
        )

    def start(self, database_id: str) -> Any:
        """Start a stopped database."""
        return self._client.request("POST", f"/databases/{segment(database_id)}/start")

    def stop(self, database_id: str) -> Any:
        """Stop a running database."""
        return self._client.request("POST", f"/databases/{segment(database_id)}/stop")

    def rotate_password(self, database_id: str, password: str | None = None) -> Any:
        """Rotate the database password, optionally forcing a specific one."""
        return self._client.request(
            "POST",
            f"/databases/{segment(database_id)}/rotate-password",
            json={"password": password} if password else {},
        )

    def create_backup(self, database_id: str) -> Any:
        """Back up the database now."""
        return self._client.request("POST", f"/databases/{segment(database_id)}/backups")

    def list_backups(self, database_id: str) -> Any:
        """List the database's backups."""
        return self._client.request("GET", f"/databases/{segment(database_id)}/backups")

    def download_backup(self, database_id: str, backup_id: str) -> Any:
        """Download a backup dump."""
        return self._client.request(
            "GET", f"/databases/{segment(database_id)}/backups/{segment(backup_id)}/download"
        )

    def restore(self, database_id: str, backup_id: str) -> Any:
        """Restore the database from a backup."""
        return self._client.request(
            "POST", f"/databases/{segment(database_id)}/restore", json={"backupId": backup_id}
        )

    def operations(self, database_id: str) -> Any:
        """List the database's long-running operations."""
        return self._client.request("GET", f"/databases/{segment(database_id)}/operations")
