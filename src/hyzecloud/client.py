"""HTTP client for the Hyze Cloud API.

Two clients ship here, and they share the same resource implementations:

* :class:`HyzeCloud` — synchronous. ``client.apps.list()`` returns the decoded body.
* :class:`AsyncHyzeCloud` — asynchronous. ``await client.apps.list()`` does the same.

Because a resource method simply returns whatever the client's ``request`` gives back, the
same ``AppsResource.list()`` yields a dict on the sync client and a coroutine on the async
one. That keeps one implementation for both, instead of a sync/async copy of every call.

Mirrors ``src/client.ts`` of the TypeScript SDK (``@hyze-cloud/sdk``).
"""

from __future__ import annotations

import json as jsonlib
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from ._url import join_url
from .errors import HyzeError, looks_like_error_payload, parse_error_body
from .resources.api_keys import ApiKeysResource
from .resources.apps import AppsResource
from .resources.databases import DatabasesResource
from .resources.github import GithubResource
from .resources.invoices import InvoicesResource
from .resources.plans import PlansResource

__all__ = ["DEFAULT_BASE_URL", "AsyncHyzeCloud", "HyzeCloud", "create_hyze_client"]

DEFAULT_BASE_URL = "https://api.hyzecloud.com/api"
DEFAULT_TIMEOUT = 60.0


def _query_value(value: Any) -> str:
    """Match JavaScript's ``String(value)``, which the TS SDK uses for query params.

    The important case is booleans: Python spells them ``True``/``False``, JavaScript
    ``true``/``false``. Sending the Python spelling would make ``?timestamps=True`` a
    different query than the TS SDK's ``?timestamps=true``.
    """
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _to_query(query: dict[str, Any] | None, workspace_id: str | None) -> dict[str, str] | None:
    merged: dict[str, Any] = dict(query or {})
    # The TS SDK checks `query.workspaceId === undefined`, and a resource that does not
    # want a scope passes `undefined` — which is what `None` means here. Testing
    # `"workspaceId" not in merged` would treat an explicit None as "the caller decided",
    # and the client-level workspace_id would be silently dropped.
    if workspace_id is not None and merged.get("workspaceId") is None:
        merged["workspaceId"] = workspace_id
    if not merged:
        return None
    return {key: _query_value(value) for key, value in merged.items() if value is not None}


def _parse_retry_after(raw: str | None) -> float | None:
    """Mirror the TS SDK's ``Number(retryAfter) || null``."""
    if not raw:
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    return number or None


def _decode_response(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "")
    payload: Any = None
    if "application/json" in content_type:
        try:
            payload = response.json()
        except ValueError:
            payload = None
    else:
        text = response.text
        payload = text
        if text:
            try:
                payload = jsonlib.loads(text)
            except ValueError:
                payload = text
    return payload


def _raise_for_error(response: httpx.Response, payload: Any) -> None:
    retry_after = _parse_retry_after(response.headers.get("retry-after"))

    if not response.is_success:
        message, code = parse_error_body(payload)
        raise HyzeError(
            message or f"Hyze API failed with status {response.status_code}",
            status=response.status_code,
            code=code,
            body=payload,
            retry_after_seconds=retry_after,
        )

    # Some endpoints answer 200 with an error-shaped body.
    if looks_like_error_payload(payload):
        message, code = parse_error_body(payload)
        raise HyzeError(
            message or "Request failed",
            status=401 if response.status_code == 200 else response.status_code,
            code=code,
            body=payload,
            retry_after_seconds=retry_after,
        )


class _BaseClient(ABC):
    """State and request building shared by the sync and async clients.

    ``request`` is abstract because the sync client returns the decoded body while the async
    client returns a coroutine. The resources only ever see this base class, which is what
    lets one ``AppsResource`` serve both.
    """

    @abstractmethod
    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json: Any = None,
        content: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send one request. The sync client returns the body; the async one, an awaitable."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        workspace_id: str | None = None,
        timeout: float | None = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
        follow_redirects: bool = True,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get("HYZE_API_KEY")
        resolved_base = (base_url or os.environ.get("HYZE_API_URL") or DEFAULT_BASE_URL).rstrip("/")

        self._api_key = resolved_key or None
        self._base_url = resolved_base
        self._workspace_id = workspace_id
        self._timeout = timeout
        self._headers: dict[str, str] = dict(headers or {})
        self._transport = transport
        self._follow_redirects = follow_redirects

        self.apps = AppsResource(self)
        self.databases = DatabasesResource(self)
        self.api_keys = ApiKeysResource(self)
        self.invoices = InvoicesResource(self)
        self.github = GithubResource(self)
        self.plans = PlansResource(self)

    @property
    def base_url(self) -> str:
        """The base URL requests are sent to, after resolving the environment fallbacks."""
        return self._base_url

    @property
    def workspace_id(self) -> str | None:
        """The default workspace scope applied to every request, when one was given."""
        return self._workspace_id

    def _prepare(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None,
        json: Any,
        content: Any,
        data: Any,
        files: Any,
        headers: dict[str, str] | None,
        timeout: float | None,
    ) -> tuple[str, str, dict[str, Any]]:
        request_headers: dict[str, str] = {
            "Accept": "application/json",
            **self._headers,
            **(headers or {}),
        }
        if self._api_key and not any(k.lower() == "authorization" for k in request_headers):
            request_headers["Authorization"] = f"Bearer {self._api_key}"

        kwargs: dict[str, Any] = {"headers": request_headers}
        params = _to_query(query, self._workspace_id)
        if params is not None:
            kwargs["params"] = params
        if timeout is not None:
            kwargs["timeout"] = timeout
        if json is not None:
            kwargs["json"] = json
        if content is not None:
            kwargs["content"] = content
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files

        return method.upper(), join_url(self._base_url, path), kwargs


class HyzeCloud(_BaseClient):
    """Synchronous client.

    Args:
        api_key: ``hyze_...`` key. Falls back to the ``HYZE_API_KEY`` env var.
        base_url: Defaults to :data:`DEFAULT_BASE_URL`, then the ``HYZE_API_URL`` env var.
        workspace_id: Default workspace/organization sent as ``workspaceId`` on every request.
        timeout: Per-request timeout in seconds. ``None`` disables it.
        headers: Extra headers sent on every request.
        transport: An ``httpx`` transport, handy for tests.

    Example:
        >>> client = HyzeCloud(api_key="hyze_...")
        >>> apps = client.apps.list()["apps"]
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        workspace_id: str | None = None,
        timeout: float | None = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        follow_redirects: bool = True,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            workspace_id=workspace_id,
            timeout=timeout,
            headers=headers,
            transport=transport,
            follow_redirects=follow_redirects,
        )
        self._http = httpx.Client(
            transport=transport, follow_redirects=follow_redirects, timeout=timeout
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json: Any = None,
        content: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send one request and decode the response. Raises :class:`HyzeError` on failure."""
        verb, url, kwargs = self._prepare(
            method,
            path,
            query=query,
            json=json,
            content=content,
            data=data,
            files=files,
            headers=headers,
            timeout=timeout,
        )
        response = self._http.request(verb, url, **kwargs)
        payload = _decode_response(response)
        _raise_for_error(response, payload)
        return payload

    def get(self, path: str, query: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self.request("GET", path, query=query, **kwargs)

    def post(self, path: str, json: Any = None, **kwargs: Any) -> Any:
        return self.request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: Any = None, **kwargs: Any) -> Any:
        return self.request("PUT", path, json=json, **kwargs)

    def patch(self, path: str, json: Any = None, **kwargs: Any) -> Any:
        return self.request("PATCH", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        """Close the underlying connection pool."""
        self._http.close()

    def __enter__(self) -> HyzeCloud:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class AsyncHyzeCloud(_BaseClient):
    """Asynchronous client — same resources, ``await`` the calls.

    Example:
        >>> client = AsyncHyzeCloud(api_key="hyze_...")
        >>> apps = (await client.apps.list())["apps"]
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        workspace_id: str | None = None,
        timeout: float | None = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        follow_redirects: bool = True,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            workspace_id=workspace_id,
            timeout=timeout,
            headers=headers,
            transport=transport,
            follow_redirects=follow_redirects,
        )
        self._http = httpx.AsyncClient(
            transport=transport, follow_redirects=follow_redirects, timeout=timeout
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json: Any = None,
        content: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send one request and decode the response. Raises :class:`HyzeError` on failure."""
        verb, url, kwargs = self._prepare(
            method,
            path,
            query=query,
            json=json,
            content=content,
            data=data,
            files=files,
            headers=headers,
            timeout=timeout,
        )
        response = await self._http.request(verb, url, **kwargs)
        payload = _decode_response(response)
        _raise_for_error(response, payload)
        return payload

    async def get(self, path: str, query: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return await self.request("GET", path, query=query, **kwargs)

    async def post(self, path: str, json: Any = None, **kwargs: Any) -> Any:
        return await self.request("POST", path, json=json, **kwargs)

    async def put(self, path: str, json: Any = None, **kwargs: Any) -> Any:
        return await self.request("PUT", path, json=json, **kwargs)

    async def patch(self, path: str, json: Any = None, **kwargs: Any) -> Any:
        return await self.request("PATCH", path, json=json, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, **kwargs)

    async def aclose(self) -> None:
        """Close the underlying connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncHyzeCloud:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()


def create_hyze_client(**kwargs: Any) -> HyzeCloud:
    """Convenience factory mirroring the TS SDK's ``createHyzeClient``."""
    return HyzeCloud(**kwargs)
