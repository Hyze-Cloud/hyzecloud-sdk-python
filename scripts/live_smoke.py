#!/usr/bin/env python3
"""Live smoke test: exercises the SDK's read paths against the real API.

Read-only by design — it never creates, deploys or deletes anything, so it is safe to point
at a workspace that matters. Write flows are covered by the unit tests instead.

Usage:
    HYZE_API_KEY=hyze_xxx python scripts/live_smoke.py
    HYZE_API_KEY=hyze_xxx HYZE_API_URL=http://127.0.0.1:3001/api python scripts/live_smoke.py

Set HYZE_SMOKE_JSON=1 for the raw payloads (api-key secrets are redacted either way).
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from typing import Any

from hyzecloud import HyzeCloud, HyzeError

REDACTED_KEYS = {"key", "apiKey", "secret", "password", "connectionString"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key in REDACTED_KEYS and value[key] else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def summarize(value: Any) -> str:
    """One line describing the shape of a payload, without dumping it."""
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if isinstance(item, list):
                parts.append(f"{key}[{len(item)}]")
            elif isinstance(item, dict):
                parts.append(f"{key}{{{len(item)}}}")
            else:
                parts.append(key)
        return " ".join(parts)
    return type(value).__name__


def main() -> int:
    if not os.environ.get("HYZE_API_KEY"):
        print("HYZE_API_KEY is not set", file=sys.stderr)
        return 2

    verbose = os.environ.get("HYZE_SMOKE_JSON") == "1"
    failures = 0

    with HyzeCloud() as client:
        print(f"base url: {client.base_url}\n")

        steps: list[tuple[str, Callable[[], Any]]] = [
            ("plans.current", client.plans.current),
            ("plans.list", client.plans.list),
            ("apps.list", client.apps.list),
            ("databases.list", client.databases.list),
            ("api_keys.list", client.api_keys.list),
            ("invoices.list", lambda: client.invoices.list(limit=5)),
            ("github.status", client.github.status),
        ]

        for name, call in steps:
            try:
                result = call()
            except HyzeError as error:
                failures += 1
                print(f"FAIL  {name}: {error.status} {error.code or '-'} {error.message}")
                continue
            print(f"ok    {name}: {summarize(result)}")
            if verbose:
                print(json.dumps(redact(result), indent=2, default=str, ensure_ascii=False))

    print()
    if failures:
        print(f"{failures} step(s) failed", file=sys.stderr)
        return 1
    print("all read paths answered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
