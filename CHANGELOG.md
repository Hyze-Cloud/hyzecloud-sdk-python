# Changelog

All notable changes to `hyze-cloud` are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [0.1.1] — 2026-09-23

### Fixed

- **The license now reaches the package metadata.** `0.1.0` shipped the `LICENSE` file but no
  license expression, so the PyPI page showed the package with no license at all. Replaced the
  deprecated classifier with the SPDX expression (`license = "MIT"` plus `license-files`), which
  the build emits as `License-Expression`.

## [0.1.0] — 2026-09-23

First release.

### Added

- **`HyzeCloud`** (synchronous) and **`AsyncHyzeCloud`**, sharing the same resources — one method
  returns the decoded body on the sync client and an awaitable on the async one.
- Resource groups: `apps`, `databases`, `api_keys`, `invoices`, `github`, `plans`.
- **`HyzeError`** carrying `status`, `code`, `body` and `retry_after_seconds`, with
  `is_rate_limited` / `is_unauthorized` / `is_not_found` helpers. A 2xx response whose body is
  shaped like an error raises too.
- `TypedDict` shapes mirroring the API responses, and `py.typed`, so editors and type checkers
  see the types.
- `scripts/check_api_routes.py` — a drift check that fails when a route the SDK calls disappears
  from the API.

### Notes

- Requires **Python 3.10+** and one dependency: `httpx`.
- Published with a signed attestation (PEP 740): you can verify that the artifact on PyPI was
  built by this repository's release workflow.
