"""Client behaviour: URL building, auth headers, query encoding, decoding and errors."""

from __future__ import annotations

import json

import httpx
import pytest

from hyzecloud import AsyncHyzeCloud, HyzeCloud, HyzeError, create_hyze_client
from hyzecloud.errors import looks_like_error_payload, parse_error_body


def client_with(handler, **kwargs) -> HyzeCloud:
    kwargs.setdefault("api_key", "hyze_test")
    transport = httpx.MockTransport(handler)
    return HyzeCloud(transport=transport, **kwargs)


def json_response(payload, status_code: int = 200, headers: dict[str, str] | None = None):
    return httpx.Response(status_code, json=payload, headers=headers or {})


# ── URL and headers ─────────────────────────────────────────────────────────


def test_default_base_url_is_the_public_api():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler).get("/plans/")
    assert str(seen[0].url) == "https://api.hyzecloud.com/api/plans/"


def test_base_url_with_trailing_slash_does_not_double_it():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler, base_url="http://127.0.0.1:3001/api///").get("plans/")
    assert str(seen[0].url) == "http://127.0.0.1:3001/api/plans/"


def test_api_key_becomes_a_bearer_header():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler, api_key="hyze_abc").get("/plans/")
    assert seen[0].headers["authorization"] == "Bearer hyze_abc"


def test_explicit_authorization_header_wins_over_the_api_key():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client = client_with(handler, headers={"Authorization": "Bearer custom"})
    client.get("/plans/")
    assert seen[0].headers["authorization"] == "Bearer custom"


def test_api_key_falls_back_to_the_environment(monkeypatch: pytest.MonkeyPatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    monkeypatch.setenv("HYZE_API_KEY", "hyze_from_env")
    HyzeCloud(transport=httpx.MockTransport(handler)).get("/plans/")
    assert seen[0].headers["authorization"] == "Bearer hyze_from_env"


def test_base_url_falls_back_to_the_environment(monkeypatch: pytest.MonkeyPatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    monkeypatch.setenv("HYZE_API_URL", "http://localhost:9999/api")
    HyzeCloud(api_key="k", transport=httpx.MockTransport(handler)).get("/plans/")
    assert str(seen[0].url) == "http://localhost:9999/api/plans/"


# ── Query encoding ──────────────────────────────────────────────────────────


def test_workspace_id_is_injected_on_every_request():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler, workspace_id="org_1").get("/apps/")
    assert seen[0].url.params["workspaceId"] == "org_1"


def test_explicit_query_workspace_id_is_not_overwritten():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler, workspace_id="org_1").get("/apps/", query={"workspaceId": "org_2"})
    assert seen[0].url.params["workspaceId"] == "org_2"


def test_booleans_use_javascript_spelling():
    """`?timestamps=True` would be a different query than the TS SDK sends."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler).get("/apps/app_1/logs", query={"timestamps": True, "tail": 50})
    assert seen[0].url.query.decode() == "timestamps=true&tail=50"


def test_none_query_values_are_dropped():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler).get("/apps/", query={"page": None, "limit": 10})
    assert seen[0].url.query.decode() == "limit=10"


# ── Bodies ──────────────────────────────────────────────────────────────────


def test_json_body_is_encoded_and_typed():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler).post("/apps/app_1/restart", json={"force": True})
    assert seen[0].headers["content-type"] == "application/json"
    assert json.loads(seen[0].content) == {"force": True}


def test_no_body_is_sent_when_none_is_given():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler).post("/apps/app_1/restart")
    assert seen[0].content == b""


# ── Decoding ────────────────────────────────────────────────────────────────


def test_json_response_is_returned_as_is():
    payload = {"success": True, "apps": [], "meta": {"total": 0}}
    assert client_with(lambda _r: json_response(payload)).get("/apps/") == payload


def test_non_json_response_that_parses_as_json_is_decoded():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text='{"success": true}', headers={"content-type": "text/plain"})

    assert client_with(handler).get("/apps/") == {"success": True}


def test_bare_string_body_survives_as_a_string():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok", headers={"content-type": "text/plain"})

    assert client_with(handler).get("/apps/") == "ok"


# ── Errors ──────────────────────────────────────────────────────────────────


def test_http_error_becomes_hyze_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return json_response({"error": "Not found", "code": "APP_NOT_FOUND"}, status_code=404)

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/nope")

    err = caught.value
    assert err.status == 404
    assert err.code == "APP_NOT_FOUND"
    assert err.message == "Not found"
    assert err.body == {"error": "Not found", "code": "APP_NOT_FOUND"}
    assert err.is_not_found is True
    assert err.is_unauthorized is False


def test_nested_error_object_is_unwrapped():
    def handler(_request: httpx.Request) -> httpx.Response:
        return json_response(
            {"error": {"message": "Invalid key", "code": "BAD_KEY"}}, status_code=401
        )

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.message == "Invalid key"
    assert caught.value.code == "BAD_KEY"
    assert caught.value.is_unauthorized is True


def test_plain_string_error_body_is_used_as_the_message():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized", headers={"content-type": "text/plain"})

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.message == "Unauthorized"
    assert caught.value.status == 401


def test_error_without_any_message_uses_the_generic_fallback():
    """`{}` carries no message, so the TS SDK lands on "Request failed" (not the status)."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={}, headers={"content-type": "application/json"})

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.message == "Request failed"
    assert caught.value.status == 500


def test_empty_error_string_falls_back_to_the_status():
    """`{"error": ""}` yields an empty message, and that is when the status is used."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": ""}, headers={"content-type": "application/json"})

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.message == "Hyze API failed with status 500"


def test_retry_after_header_is_parsed():
    def handler(_request: httpx.Request) -> httpx.Response:
        return json_response({"error": "slow down"}, status_code=429, headers={"retry-after": "30"})

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.retry_after_seconds == 30
    assert caught.value.is_rate_limited is True


def test_retry_after_zero_is_reported_as_absent():
    """The TS SDK computes `Number(header) || null`, so "0" collapses to null."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return json_response({"error": "nope"}, status_code=429, headers={"retry-after": "0"})

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.retry_after_seconds is None


def test_200_with_error_shaped_body_still_raises():
    def handler(_request: httpx.Request) -> httpx.Response:
        return json_response({"success": False, "error": "Unauthorized"})

    with pytest.raises(HyzeError) as caught:
        client_with(handler).get("/apps/")
    assert caught.value.status == 401


def test_looks_like_error_payload_matches_the_ts_rules():
    assert looks_like_error_payload({"success": False}) is True
    assert looks_like_error_payload({"error": "boom"}) is True
    assert looks_like_error_payload({"error": {"message": "boom"}}) is True
    assert looks_like_error_payload("Unauthorized") is True
    assert looks_like_error_payload("error: nope") is True
    assert looks_like_error_payload({"success": True, "apps": []}) is False
    assert looks_like_error_payload({"error": ""}) is False
    assert looks_like_error_payload(None) is False
    assert looks_like_error_payload(42) is False


def test_parse_error_body_precedence():
    assert parse_error_body("  boom  ") == ("boom", None)
    assert parse_error_body("") == ("Request failed", None)
    assert parse_error_body({"error": "a", "code": "C"}) == ("a", "C")
    assert parse_error_body({"error": {"message": "a", "code": "C"}}) == ("a", "C")
    assert parse_error_body({"message": "a", "code": "C"}) == ("a", "C")
    assert parse_error_body({"code": "C"}) == ("Request failed", "C")


# ── Client plumbing ─────────────────────────────────────────────────────────


def test_context_manager_closes_the_client():
    with client_with(lambda _r: json_response({"success": True})) as client:
        client.get("/apps/")
    assert client._http.is_closed


def test_factory_returns_a_sync_client():
    assert isinstance(create_hyze_client(api_key="k"), HyzeCloud)


def test_timeout_is_forwarded():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True})

    client_with(handler, timeout=12.5).get("/apps/")
    assert seen[0].extensions["timeout"] == {
        "connect": 12.5,
        "read": 12.5,
        "write": 12.5,
        "pool": 12.5,
    }


# ── Async ───────────────────────────────────────────────────────────────────


async def test_async_client_uses_the_same_resources():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"success": True, "apps": [], "meta": {"total": 0}})

    async with AsyncHyzeCloud(
        api_key="hyze_async", transport=httpx.MockTransport(handler), workspace_id="org_9"
    ) as client:
        result = await client.apps.list()

    assert result["success"] is True
    assert seen[0].headers["authorization"] == "Bearer hyze_async"
    assert seen[0].url.params["workspaceId"] == "org_9"


async def test_async_client_raises_the_same_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return json_response({"error": "Not found"}, status_code=404)

    async with AsyncHyzeCloud(api_key="k", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(HyzeError) as caught:
            await client.apps.get("nope")
    assert caught.value.is_not_found is True
