"""Official Python SDK for the Hyze Cloud API.

    from hyzecloud import HyzeCloud

    client = HyzeCloud(api_key="hyze_...")
    for app in client.apps.list()["apps"]:
        print(app["name"], app["status"])

An async client with the same surface is available as :class:`AsyncHyzeCloud`:

    from hyzecloud import AsyncHyzeCloud

    async with AsyncHyzeCloud() as client:   # reads HYZE_API_KEY
        apps = await client.apps.list()

This mirrors the TypeScript SDK (``@hyze-cloud/sdk``): same resources, same routes, same
error shape.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from .client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, AsyncHyzeCloud, HyzeCloud, create_hyze_client
from .errors import HyzeError, looks_like_error_payload, parse_error_body
from .resources import (
    ApiKeysResource,
    AppsResource,
    DatabasesResource,
    GithubResource,
    InvoicesResource,
    PlansResource,
)
from .types import (
    ApiKeyCreated,
    ApiKeyCreateResponse,
    ApiKeyItem,
    ApiKeysListResponse,
    ApiKeyUpdateResponse,
    AppDeployment,
    AppDeploymentsResponse,
    AppDeploymentStatus,
    AppDetail,
    AppDetailResponse,
    AppEnvResponse,
    AppListItem,
    AppLogsResponse,
    AppsListResponse,
    BillingInterval,
    ContainerStats,
    CreateApiKeyInput,
    CreateDatabaseInput,
    CreatePixInvoiceInput,
    CurrentPlanResponse,
    DatabaseEngine,
    DatabaseItem,
    DatabaseResponse,
    DatabasesListResponse,
    DeployFromRepoInput,
    DeployFromZipInput,
    DeployRepository,
    GithubStatusResponse,
    InvoiceBilling,
    InvoiceDetail,
    InvoiceDetailResponse,
    InvoiceListItem,
    InvoicePlanSummary,
    InvoicesListResponse,
    PlanInfo,
    PlanPriceInfo,
    PlansListResponse,
    PlanUsage,
    RequestOptions,
    Runtime,
    UpdateApiKeyInput,
    UpdateAppSettingsInput,
)

try:
    __version__ = _version("hyze-cloud")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0"

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "ApiKeyCreateResponse",
    "ApiKeyCreated",
    "ApiKeyItem",
    "ApiKeyUpdateResponse",
    "ApiKeysListResponse",
    "ApiKeysResource",
    "AppDeployment",
    "AppDeploymentStatus",
    "AppDeploymentsResponse",
    "AppDetail",
    "AppDetailResponse",
    "AppEnvResponse",
    "AppListItem",
    "AppLogsResponse",
    "AppsListResponse",
    "AppsResource",
    "AsyncHyzeCloud",
    "BillingInterval",
    "ContainerStats",
    "CreateApiKeyInput",
    "CreateDatabaseInput",
    "CreatePixInvoiceInput",
    "CurrentPlanResponse",
    "DatabaseEngine",
    "DatabaseItem",
    "DatabaseResponse",
    "DatabasesListResponse",
    "DatabasesResource",
    "DeployFromRepoInput",
    "DeployFromZipInput",
    "DeployRepository",
    "GithubResource",
    "GithubStatusResponse",
    "HyzeCloud",
    "HyzeError",
    "InvoiceBilling",
    "InvoiceDetail",
    "InvoiceDetailResponse",
    "InvoiceListItem",
    "InvoicePlanSummary",
    "InvoicesListResponse",
    "InvoicesResource",
    "PlanInfo",
    "PlanPriceInfo",
    "PlanUsage",
    "PlansListResponse",
    "PlansResource",
    "RequestOptions",
    "Runtime",
    "UpdateApiKeyInput",
    "UpdateAppSettingsInput",
    "__version__",
    "create_hyze_client",
    "looks_like_error_payload",
    "parse_error_body",
]
