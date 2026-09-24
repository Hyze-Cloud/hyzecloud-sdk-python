# hyze-cloud

[![CI](https://github.com/Hyze-Cloud/hyzecloud-sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Hyze-Cloud/hyzecloud-sdk-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hyze-cloud)](https://pypi.org/project/hyze-cloud/)
[![Python versions](https://img.shields.io/pypi/pyversions/hyze-cloud)](https://pypi.org/project/hyze-cloud/)
[![license](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

Official **Python** SDK for the [Hyze Cloud API](https://docs.hyzecloud.app).

- **Sync and async** clients with the same surface — `client.apps.list()` or `await`
- Typed helpers for apps, databases, API keys, invoices, GitHub and plans
- One dependency (`httpx`), and it is the only one
- Consistent `HyzeError` carrying status, code and `Retry-After`
- Ships `py.typed`, so editors and type checkers see the shapes

This is a port of the TypeScript SDK ([`@hyze-cloud/sdk`](https://github.com/Hyze-Cloud/hyzecloud-sdk-ts)):
same resources, same routes, same error shape. The one naming difference is deliberate — Python
callers use `snake_case` (`memory_mb`) and the SDK translates it to the API's `camelCase`
(`memoryMB`).

## Install

```bash
pip install hyze-cloud
# or
uv add hyze-cloud
```

Requires **Python 3.10+**.

## Quickstart

```python
from hyzecloud import HyzeCloud, HyzeError

client = HyzeCloud(
    # api_key="hyze_...",                       # defaults to $HYZE_API_KEY
    # base_url="https://api.hyzecloud.com/api", # the default
    # workspace_id="org_...",                   # optional scope
)

for app in client.apps.list()["apps"]:
    print(app["name"], app["status"])

try:
    client.apps.restart("app_001")
except HyzeError as err:
    print(err.status, err.code, err.message)
    if err.is_rate_limited:
        print("retry after", err.retry_after_seconds)
    raise
```

Close the client when you are done, or use it as a context manager:

```python
with HyzeCloud() as client:
    client.plans.current()
```

## Async

The same calls, awaited. `AsyncHyzeCloud` is the client to reach for inside FastAPI, aiohttp or
any asyncio program:

```python
import asyncio
from hyzecloud import AsyncHyzeCloud


async def main() -> None:
    async with AsyncHyzeCloud() as client:
        apps = await client.apps.list()
        print(len(apps["apps"]))


asyncio.run(main())
```

## Apps

```python
# List / get
apps = client.apps.list()["apps"]
detail = client.apps.get("app_001")["container"]

# Lifecycle
client.apps.start("app_001")
client.apps.stop("app_001")
client.apps.restart("app_001")

# Logs, env, deploy history
client.apps.logs("app_001", tail=200, timestamps=True)
client.apps.get_env("app_001")
client.apps.set_env("app_001", {"NODE_ENV": "production"})
client.apps.deployments("app_001", limit=30)

# Deploy from a ZIP — a path, raw bytes, or an open file all work.
# A path is read into memory; pass an open file for a large archive (it gets streamed).
client.apps.deploy_from_zip(
    file="./app.zip",
    name="my-api",
    runtime="python",
    memory_mb=512,
    expose_port=8000,
    subdomain="my-api",
    # startup_command omitted (or "auto") -> Hyze detects the start command
)

# Detect the env vars of a ZIP without deploying it
client.apps.inspect_env("./app.zip")

# Deploy from a connected GitHub repository
client.apps.deploy_from_repo(
    name="my-api",
    runtime="python",
    memory_mb=512,
    repository={"id": 123, "owner": "acme", "name": "api", "branch": "main"},
)

# Backups
client.apps.create_backup("app_001")
client.apps.list_backups("app_001")
client.apps.restore_backup("app_001", "backup_001")
```

## Databases

```python
client.databases.create(name="prod-postgres", engine="postgresql", memory_mb=1024, storage_gb=20)
client.databases.list()
client.databases.stats("db_001")
client.databases.rotate_password("db_001")
client.databases.create_backup("db_001")
client.databases.restore("db_001", "backup_001")
```

## API keys, invoices, GitHub, plans

```python
keys = client.api_keys.list()["keys"]
created = client.api_keys.create(name="ci")
# created["key"]["key"] is the one-time secret — it is never returned again

invoices = client.invoices.list()["invoices"]
pix = client.invoices.create_pix(plan_id="pro", interval="month")
# pix["invoice"]["brCode"] / ["brCodeBase64"] for the checkout screen
client.invoices.status(pix["invoice"]["id"], include_pix=True)

client.github.status()
client.github.repos()
client.github.branches("acme", "api")
client.github.detect_runtime("acme", "api", branch="main")

current = client.plans.current()  # plan + usage, no nested apps/databases lists
client.plans.list()
```

## Error handling

Every failure raises `HyzeError`, including a 2xx response whose body is shaped like an error.

| Attribute | Meaning |
| --- | --- |
| `status` | HTTP status (401 when a 2xx body looked like an error) |
| `code` | Structured code from the payload, when the API sent one |
| `message` | Human-readable message |
| `body` | The decoded payload, untouched |
| `retry_after_seconds` | From the `Retry-After` header, when present |

`is_rate_limited` (`429`), `is_unauthorized` (`401`/`403`) and `is_not_found` (`404`) are there so
callers do not have to compare numbers by hand.

## Low-level access

```python
client.get("/apps/")
client.post("/apps/app_001/restart")
client.request("GET", "/apps/", query={"workspaceId": "org_1"})
```

## Environment

| Variable | Description |
| --- | --- |
| `HYZE_API_KEY` | Default API key when `api_key` is omitted |
| `HYZE_API_URL` | Override the base URL (default `https://api.hyzecloud.com/api`) |

## Development

```bash
uv venv && uv pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m mypy
.venv/bin/python -m ruff check .
.venv/bin/python scripts/check_api_routes.py   # are the routes this SDK calls still there?
```

`check_api_routes.py` hits the production API **unauthenticated**: a 404 means the route is gone,
any other status (401/400/…) means it exists. It runs on every PR and before publishing — a
published client calling a dead route is a 404 for the user.

### Live smoke test

Exercises the read paths against the real API with your key:

```bash
HYZE_API_KEY=hyze_xxx .venv/bin/python scripts/live_smoke.py
```

## Release

The tag drives the version: `vX.Y.Z` must match `pyproject.toml`, otherwise the workflow aborts
before publishing.

```bash
# bump the version, then
git tag v0.1.1 && git push origin v0.1.1
```

`release.yml` runs ruff + mypy + pytest + `check_api_routes.py`, builds the sdist and the wheel,
and publishes to PyPI through **Trusted Publishing** (OIDC) — there is no API token stored anywhere.

## Docs

- [Hyze Cloud Docs](https://docs.hyzecloud.app)
- [API introduction](https://docs.hyzecloud.app/api-reference/introduction)
- [Rate limits](https://docs.hyzecloud.app/en/concepts/rate-limits)
- [Changelog](./CHANGELOG.md)

## License

MIT
