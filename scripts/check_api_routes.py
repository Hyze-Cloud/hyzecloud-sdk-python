#!/usr/bin/env python3
"""Drift check: does every route this SDK calls still exist on the API?

Why it exists: this repo is public and the package goes to PyPI, but the API lives in
another repository. Nothing stops the API from renaming or removing an endpoint and the
published client turning into a 404 at runtime — silent drift. This closes that gap without
needing an API key:

  * extracts (method, path) from ``src/hyzecloud/resources/*.py``
  * calls each path WITHOUT authentication, with the right method and a placeholder id
  * 404 = the route no longer exists -> FAIL
    any other status (401/400/403/405/...) = the route exists (it just wants auth/a valid body)

The distinction is reliable because authentication runs before route resolution on this API.
Negative control: an invented route must answer 404, so the check cannot pass by accident.

Usage:
    python scripts/check_api_routes.py [--base-url https://api.hyzecloud.com/api]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx

PLACEHOLDER = "00000000-0000-0000-0000-000000000000"
CONTROL_PATH = "/rota-inventada-do-ci"

CALL_RE = re.compile(
    r'self\._client\.request\(\s*"([A-Z]+)"\s*,\s*f?"([^"]*)"',
)

SEGMENT_RE = re.compile(r"\{segment\([^}]*\)\}")


def collect_calls(resources_dir: Path) -> list[tuple[str, str, str]]:
    """Return ``(method, path, source)`` for every call the resources make."""
    calls: list[tuple[str, str, str]] = []
    for path in sorted(resources_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in CALL_RE.finditer(text):
            method, raw = match.group(1), match.group(2)
            if not raw.startswith("/"):
                continue
            calls.append(
                (method, SEGMENT_RE.sub(PLACEHOLDER, raw), f"src/hyzecloud/resources/{path.name}")
            )
    return sorted(set(calls), key=lambda c: (c[1], c[0]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://api.hyzecloud.com/api")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    resources_dir = Path(__file__).resolve().parent.parent / "src" / "hyzecloud" / "resources"
    calls = collect_calls(resources_dir)

    if not calls:
        print(
            "no calls found in src/hyzecloud/resources — did the extractor break?", file=sys.stderr
        )
        return 1

    gone: list[tuple[str, str, str]] = []
    failures = False
    rows: list[str] = []

    with httpx.Client(timeout=20.0, follow_redirects=False) as client:
        # Negative control first: if an invented route does not 404, the signal is worthless.
        control = client.request("GET", f"{base}{CONTROL_PATH}")
        if control.status_code != 404:
            print(
                f"negative control answered {control.status_code}, expected 404 — "
                "the check cannot tell a live route from a dead one",
                file=sys.stderr,
            )
            return 1

        for method, path, source in calls:
            try:
                response = client.request(
                    method,
                    f"{base}{path}",
                    headers={"content-type": "application/json"},
                    content=b"{}" if method not in ("GET", "DELETE") else None,
                )
            except httpx.HTTPError as error:
                print(f"   NETWORK ERROR on {method} {path}: {error}", file=sys.stderr)
                failures = True
                continue

            if response.status_code == 404:
                gone.append((method, path, source))
            rows.append(f"{response.status_code:>3}  {method:<6} {path}")

    for row in rows:
        print(f"   {row}")
    print(f"\n   {len(calls)} routes checked on {base}")

    if gone:
        print(f"\nDRIFT: {len(gone)} route(s) this SDK calls no longer exist:", file=sys.stderr)
        for method, path, source in gone:
            print(f"   {method} {path}   ({source})", file=sys.stderr)
        print(
            "\nFix the SDK (or the API) before publishing — a published client calling a "
            "dead route is a 404 for the user.",
            file=sys.stderr,
        )
        return 1

    if failures:
        return 1

    print("   ok: no route this SDK calls has disappeared from the API")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
