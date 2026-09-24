"""Invoices and PIX checkout.

Mirrors ``src/resources/invoices.ts`` of the TypeScript SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._url import segment

if TYPE_CHECKING:
    from ..client import _BaseClient

__all__ = ["InvoicesResource"]


class InvoicesResource:
    """``client.invoices`` — everything under ``/invoices``."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def list(self, *, limit: int | None = None) -> Any:
        """List the workspace's invoices, newest first."""
        return self._client.request("GET", "/invoices/", query={"limit": limit})

    def create_pix(self, *, plan_id: str, interval: str | None = None) -> Any:
        """Open a PIX checkout for a plan. The response carries the BR Code."""
        body: dict[str, Any] = {"planId": plan_id}
        if interval is not None:
            body["interval"] = interval
        return self._client.request("POST", "/invoices/pix", json=body)

    def status(self, invoice_id: str, *, include_pix: bool | None = None) -> Any:
        """Poll an invoice. Pass ``include_pix=True`` to get the BR Code back."""
        return self._client.request(
            "GET",
            f"/invoices/{segment(invoice_id)}/status",
            query={"includePix": include_pix},
        )
