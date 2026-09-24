"""Resource groups, one per API area.

Each group is written once and works with both clients: a method returns whatever the
client's ``request`` returns, so ``client.apps.list()`` is a dict on :class:`HyzeCloud`
and a coroutine on :class:`AsyncHyzeCloud`.
"""

from __future__ import annotations

from .api_keys import ApiKeysResource
from .apps import AppsResource
from .databases import DatabasesResource
from .github import GithubResource
from .invoices import InvoicesResource
from .plans import PlansResource

__all__ = [
    "ApiKeysResource",
    "AppsResource",
    "DatabasesResource",
    "GithubResource",
    "InvoicesResource",
    "PlansResource",
]
