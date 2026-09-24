"""Resource routing: method, path, encoding, and the multipart/JSON bodies."""

from __future__ import annotations

import json

import httpx
import pytest

from hyzecloud import HyzeCloud


@pytest.fixture
def calls() -> list[httpx.Request]:
    return []


@pytest.fixture
def client(calls: list[httpx.Request]) -> HyzeCloud:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200, json={"success": True}, headers={"content-type": "application/json"}
        )

    return HyzeCloud(api_key="hyze_test", transport=httpx.MockTransport(handler))


def hit(request: httpx.Request) -> tuple[str, str]:
    return request.method, request.url.path


APP_ID = "app_001"
DB_ID = "db_001"
KEY_ID = "key_001"
INVOICE_ID = "inv_001"
BACKUP_ID = "bkp_001"


# ── Every route, with the method the API expects ────────────────────────────


def test_apps_routes(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.apps.list()
    client.apps.get(APP_ID)
    client.apps.delete(APP_ID)
    client.apps.start(APP_ID)
    client.apps.stop(APP_ID)
    client.apps.restart(APP_ID)
    client.apps.logs(APP_ID)
    client.apps.deployments(APP_ID)
    client.apps.get_env(APP_ID)
    client.apps.set_env(APP_ID, {"A": "1"})
    client.apps.update_settings(APP_ID, name="x")
    client.apps.deploy_from_repo(name="n", runtime="python", memory_mb=512, repository={})
    client.apps.inspect_env(b"zip")
    client.apps.create_backup(APP_ID)
    client.apps.list_backups(APP_ID)
    client.apps.delete_backups(APP_ID)
    client.apps.restore_backup(APP_ID, BACKUP_ID)
    client.apps.download_backup(APP_ID, BACKUP_ID)

    assert [hit(r) for r in calls] == [
        ("GET", "/api/apps/"),
        ("GET", f"/api/apps/{APP_ID}"),
        ("DELETE", f"/api/apps/{APP_ID}"),
        ("POST", f"/api/apps/{APP_ID}/start"),
        ("POST", f"/api/apps/{APP_ID}/stop"),
        ("POST", f"/api/apps/{APP_ID}/restart"),
        ("GET", f"/api/apps/{APP_ID}/logs"),
        ("GET", f"/api/apps/{APP_ID}/deployments"),
        ("GET", f"/api/apps/{APP_ID}/env"),
        ("PUT", f"/api/apps/{APP_ID}/env"),
        ("PUT", f"/api/apps/{APP_ID}/settings"),
        ("POST", "/api/apps/deploy-from-repo"),
        ("POST", "/api/apps/inspect-env"),
        ("POST", f"/api/apps/{APP_ID}/backup"),
        ("GET", f"/api/apps/{APP_ID}/backups"),
        ("DELETE", f"/api/apps/{APP_ID}/backups"),
        ("POST", f"/api/apps/{APP_ID}/backups/restore"),
        ("GET", f"/api/apps/{APP_ID}/backups/{BACKUP_ID}/download"),
    ]


def test_databases_routes(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.databases.list()
    client.databases.get(DB_ID)
    client.databases.create(name="n", engine="postgresql")
    client.databases.delete(DB_ID)
    client.databases.update_settings(DB_ID, name="x")
    client.databases.stats(DB_ID)
    client.databases.logs(DB_ID)
    client.databases.start(DB_ID)
    client.databases.stop(DB_ID)
    client.databases.rotate_password(DB_ID)
    client.databases.create_backup(DB_ID)
    client.databases.list_backups(DB_ID)
    client.databases.download_backup(DB_ID, BACKUP_ID)
    client.databases.restore(DB_ID, BACKUP_ID)
    client.databases.operations(DB_ID)

    assert [hit(r) for r in calls] == [
        ("GET", "/api/databases/"),
        ("GET", f"/api/databases/{DB_ID}"),
        ("POST", "/api/databases/"),
        ("DELETE", f"/api/databases/{DB_ID}"),
        ("PATCH", f"/api/databases/{DB_ID}/settings"),
        ("GET", f"/api/databases/{DB_ID}/stats"),
        ("GET", f"/api/databases/{DB_ID}/logs"),
        ("POST", f"/api/databases/{DB_ID}/start"),
        ("POST", f"/api/databases/{DB_ID}/stop"),
        ("POST", f"/api/databases/{DB_ID}/rotate-password"),
        ("POST", f"/api/databases/{DB_ID}/backups"),
        ("GET", f"/api/databases/{DB_ID}/backups"),
        ("GET", f"/api/databases/{DB_ID}/backups/{BACKUP_ID}/download"),
        ("POST", f"/api/databases/{DB_ID}/restore"),
        ("GET", f"/api/databases/{DB_ID}/operations"),
    ]


def test_api_keys_routes(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.api_keys.list()
    client.api_keys.create(name="ci")
    client.api_keys.update(KEY_ID, enabled=False)
    client.api_keys.delete(KEY_ID)

    assert [hit(r) for r in calls] == [
        ("GET", "/api/api-keys/"),
        ("POST", "/api/api-keys/"),
        ("PUT", f"/api/api-keys/{KEY_ID}"),
        ("DELETE", f"/api/api-keys/{KEY_ID}"),
    ]


def test_github_routes(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.github.status()
    client.github.install_url()
    client.github.disconnect()
    client.github.repos()
    client.github.branches("acme", "api")
    client.github.detect_runtime("acme", "api", branch="main")

    assert [hit(r) for r in calls] == [
        ("GET", "/api/integrations/github/status"),
        ("GET", "/api/integrations/github/install-url"),
        ("DELETE", "/api/integrations/github/connection"),
        ("GET", "/api/integrations/github/repos"),
        ("GET", "/api/integrations/github/repos/acme/api/branches"),
        ("GET", "/api/integrations/github/repos/acme/api/runtime"),
    ]


def test_invoices_and_plans_routes(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.invoices.list()
    client.invoices.create_pix(plan_id="pro")
    client.invoices.status(INVOICE_ID)
    client.plans.current()
    client.plans.list()

    assert [hit(r) for r in calls] == [
        ("GET", "/api/invoices/"),
        ("POST", "/api/invoices/pix"),
        ("GET", f"/api/invoices/{INVOICE_ID}/status"),
        ("GET", "/api/plans/current"),
        ("GET", "/api/plans/"),
    ]


# ── Encoding ────────────────────────────────────────────────────────────────


def test_ids_are_percent_encoded(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    """The TS SDK wraps every id in encodeURIComponent; a raw '/' would change the route."""
    client.apps.get("a b/c")
    client.databases.get("db?x=1")

    assert calls[0].url.raw_path == b"/api/apps/a%20b%2Fc"
    assert calls[1].url.raw_path == b"/api/databases/db%3Fx%3D1"


def test_github_owner_and_repo_are_encoded(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.github.branches("ac me", "a/pic")
    assert calls[0].url.raw_path == b"/api/integrations/github/repos/ac%20me/a%2Fpic/branches"


# ── Bodies ──────────────────────────────────────────────────────────────────


def test_deploy_from_zip_sends_multipart_with_the_api_field_names(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.apps.deploy_from_zip(
        file=b"PK\x03\x04zip",
        name="my-api",
        runtime="python",
        memory_mb=512,
        expose_port=8000,
        subdomain="my-api",
        env_vars={"A": "1"},
        auto_restart=True,
        filename="bundle.zip",
    )

    request = calls[0]
    assert request.method == "POST"
    assert request.url.path == "/api/apps/deploy"
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")

    body = request.content.decode("latin-1")
    for expected in (
        'name="name"',
        'name="runtime"',
        'name="memoryMB"',
        'name="startupCommand"',
        'name="exposePort"',
        'name="subdomain"',
        'name="envVars"',
        'name="autoRestart"',
        'name="file"',
        'filename="bundle.zip"',
    ):
        assert expected in body, expected

    assert "my-api" in body
    assert "python" in body
    assert "512" in body
    assert "8000" in body
    assert "true" in body


def test_deploy_from_zip_defaults_the_startup_command_to_auto(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.apps.deploy_from_zip(file=b"x", name="n", runtime="python", memory_mb=256)
    body = calls[0].content.decode("latin-1")
    assert "auto" in body


def test_deploy_from_zip_keeps_a_custom_startup_command(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.apps.deploy_from_zip(
        file=b"x",
        name="n",
        runtime="python",
        memory_mb=256,
        startup_command="  uvicorn main:app  ",
    )
    assert "uvicorn main:app" in calls[0].content.decode("latin-1")


def test_set_env_wraps_the_map_in_env_vars(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.apps.set_env(APP_ID, {"NODE_ENV": "production"})
    assert json.loads(calls[0].content) == {"envVars": {"NODE_ENV": "production"}}


def test_update_settings_sends_only_what_was_passed(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.apps.update_settings(APP_ID, memory_mb=1024)
    assert json.loads(calls[0].content) == {"memoryMB": 1024}


def test_restore_backup_sends_the_backup_id(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.databases.restore(DB_ID, BACKUP_ID)
    assert json.loads(calls[0].content) == {"backupId": BACKUP_ID}


def test_rotate_password_without_a_password_sends_an_empty_object(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.databases.rotate_password(DB_ID)
    assert json.loads(calls[0].content) == {}


def test_rotate_password_with_a_password_sends_it(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.databases.rotate_password(DB_ID, "s3cret")
    assert json.loads(calls[0].content) == {"password": "s3cret"}


def test_create_pix_sends_the_interval_when_given(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.invoices.create_pix(plan_id="pro", interval="year")
    assert json.loads(calls[0].content) == {"planId": "pro", "interval": "year"}


# ── Queries on the resources ────────────────────────────────────────────────


def test_logs_query_is_forwarded(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.apps.logs(APP_ID, tail=200, timestamps=True, since="2026-01-01")
    assert calls[0].url.query.decode() == "tail=200&timestamps=true&since=2026-01-01"


def test_inspect_env_uses_the_default_filename(
    client: HyzeCloud, calls: list[httpx.Request]
) -> None:
    client.apps.inspect_env(b"zip")
    assert 'filename="app.zip"' in calls[0].content.decode("latin-1")


def test_apps_list_can_scope_by_organization(client: HyzeCloud, calls: list[httpx.Request]) -> None:
    client.apps.list(organization_id="org_1")
    assert calls[0].url.params["organizationId"] == "org_1"
