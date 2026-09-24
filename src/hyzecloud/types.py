"""Typed shapes of the Hyze Cloud API responses and request bodies.

TypedDicts describe what the API returns: the SDK hands back the decoded JSON untouched, so
these are hints for editors and type checkers, not a validation layer. A field the API adds
later is simply not described here yet — it never raises.

Mirrors ``src/types.ts`` of the TypeScript SDK (``@hyze-cloud/sdk``).
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = [
    "ApiKeyCreateResponse",
    "ApiKeyCreated",
    "ApiKeyItem",
    "ApiKeyUpdateResponse",
    "ApiKeysListResponse",
    "AppDeployment",
    "AppDeploymentsResponse",
    "AppDetail",
    "AppDetailResponse",
    "AppEnvResponse",
    "AppListItem",
    "AppLogsResponse",
    "AppsListResponse",
    "BillingInterval",
    "ContainerStats",
    "CreateApiKeyInput",
    "CreateDatabaseInput",
    "CreatePixInvoiceInput",
    "CurrentPlanResponse",
    "DatabaseItem",
    "DatabaseResponse",
    "DatabasesListResponse",
    "DeployFromRepoInput",
    "DeployFromZipInput",
    "DeployRepository",
    "GithubStatusResponse",
    "InvoiceBilling",
    "InvoiceDetail",
    "InvoiceDetailResponse",
    "InvoiceListItem",
    "InvoicePlanSummary",
    "InvoicesListResponse",
    "PlanInfo",
    "PlanPriceInfo",
    "PlanUsage",
    "PlansListResponse",
    "RequestOptions",
    "Runtime",
    "UpdateApiKeyInput",
    "UpdateAppSettingsInput",
]

Runtime = Literal["node", "bun", "python"]
DatabaseEngine = Literal["postgresql", "mysql", "mongodb", "redis"]
BillingInterval = Literal["month", "quarter", "semiannual", "year"]

# The API returns free-form status strings; these are the values known today.
AppListStatus = str
DatabaseStatus = str
InvoiceStatus = str
AppDeploymentStatus = Literal["queued", "building", "success", "failed", "superseded", "cancelled"]


class RequestOptions(TypedDict, total=False):
    """Per-request overrides accepted by :meth:`HyzeCloud.request`."""

    query: dict[str, Any]
    headers: dict[str, str]
    timeout: float


# ── Apps ────────────────────────────────────────────────────────────────────


class AppListItem(TypedDict):
    """App row from ``GET /apps/``."""

    id: str
    name: str
    workspaceId: str
    runtime: str
    status: str
    ramMB: int
    domain: str | None
    createdAt: str
    updatedAt: str


class ContainerStats(TypedDict):
    cpuPercent: float
    memoryMB: float
    memoryLimitMB: float
    pids: int
    networkRxBytes: int
    networkTxBytes: int


class AppDetail(TypedDict, total=False):
    """App detail from ``GET /apps/:id`` (public shape; no Docker internals)."""

    id: str
    name: str
    status: str
    createdAt: str
    runtime: str
    startupCommand: str
    exposePort: int
    subdomain: str
    publishedPort: int
    publicUrl: str
    autoRestart: bool
    sourceType: str
    sourceRepoOwner: str
    sourceRepoName: str
    sourceBranch: str
    sourcePath: str
    autoDeploy: bool
    autoBackup: bool
    lastAutoBackupAt: str
    lastDeployedCommitSha: str
    stats: ContainerStats


class AppsListResponse(TypedDict):
    success: bool
    apps: list[AppListItem]
    meta: dict[str, int]


class AppDetailResponse(TypedDict):
    success: bool
    container: AppDetail


class AppLogsResponse(TypedDict):
    success: bool
    logs: str


class AppEnvResponse(TypedDict):
    success: bool
    envVars: dict[str, str]


class AppDeployment(TypedDict, total=False):
    """One deploy row — mirrors ``application_deploy_logs.status`` on the API."""

    id: str
    status: str
    title: str | None
    description: str | None
    error: str | None
    errorCode: str | None
    logs: str | None
    logsStatus: str | None
    createdAt: str
    commitSha: str | None
    repository: str | None
    branch: str | None
    source: str | None
    retryOfDeploymentId: str | None
    exitCode: int | None
    oomKilled: bool | None
    waitingReason: str | None
    waitingDetail: str | None
    queuePosition: int | None
    queuePositionOnMachine: int | None


class AppDeploymentsResponse(TypedDict):
    success: bool
    deployments: list[AppDeployment]
    currentDeploymentId: str | None
    activeDeploymentId: str | None
    meta: dict[str, int]


class DeployFromZipInput(TypedDict, total=False):
    """Body of :meth:`hyzecloud.resources.apps.AppsResource.deploy_from_zip`."""

    file: Any
    filename: str
    name: str
    runtime: str
    memoryMB: int
    startupCommand: str
    envVars: dict[str, str] | str
    exposePort: int
    subdomain: str
    autoRestart: bool
    machineId: str
    workspaceId: str


class DeployRepository(TypedDict, total=False):
    id: str | int
    owner: str
    name: str
    branch: str
    path: str
    githubInstallationId: str | int


class DeployFromRepoInput(TypedDict, total=False):
    name: str
    runtime: str
    memoryMB: int
    startupCommand: str
    envVars: dict[str, str] | str
    exposePort: int
    subdomain: str
    autoDeploy: bool
    machineId: str
    workspaceId: str
    repository: DeployRepository


class UpdateAppSettingsInput(TypedDict, total=False):
    name: str
    runtime: str
    memoryMB: int
    startupCommand: str
    exposePort: int | None
    subdomain: str | None
    autoRestart: bool


# ── Databases ───────────────────────────────────────────────────────────────


class DatabaseItem(TypedDict, total=False):
    """Public database row — no Docker container id, volume or internal host."""

    id: str
    name: str
    engine: str
    version: str
    status: str
    memoryMB: int
    storageGB: float
    host: str | None
    port: int | None
    username: str
    databaseName: str
    connectionString: str | None
    lastError: str | None
    createdAt: str
    updatedAt: str


class DatabasesListResponse(TypedDict):
    success: bool
    databases: list[DatabaseItem]


class DatabaseResponse(TypedDict, total=False):
    success: bool
    database: DatabaseItem
    operationId: str


class CreateDatabaseInput(TypedDict, total=False):
    name: str
    engine: str
    version: str
    memoryMB: int
    storageGB: float
    username: str
    password: str
    databaseName: str
    machineId: str
    workspaceId: str


# ── API keys ────────────────────────────────────────────────────────────────


class ApiKeyItem(TypedDict, total=False):
    id: str
    name: str | None
    start: str | None
    prefix: str | None
    enabled: bool
    remaining: int | None
    lastRequest: str | None
    expiresAt: str | None
    createdAt: str | None
    updatedAt: str | None


class ApiKeyCreated(ApiKeyItem, total=False):
    """Returned only on create — the secret is shown once."""

    key: str


class ApiKeysListResponse(TypedDict):
    success: bool
    keys: list[ApiKeyItem]


class ApiKeyCreateResponse(TypedDict):
    success: bool
    key: ApiKeyCreated


class ApiKeyUpdateResponse(TypedDict):
    success: bool
    key: ApiKeyItem


class CreateApiKeyInput(TypedDict, total=False):
    name: str
    expiresIn: int | None
    remaining: int
    metadata: dict[str, Any]


class UpdateApiKeyInput(TypedDict, total=False):
    name: str
    enabled: bool
    remaining: int
    metadata: dict[str, Any]


# ── Invoices ────────────────────────────────────────────────────────────────


class InvoicePlanSummary(TypedDict):
    id: str
    name: str
    price: float


class InvoiceBilling(TypedDict, total=False):
    interval: str
    months: int
    discountPercent: float
    priceCents: int
    planExpiresAt: str | None
    planPriceId: str | None


class InvoiceListItem(TypedDict, total=False):
    """List item — no PIX payload or payment-provider internals."""

    id: str
    planId: str
    method: str
    amount: float
    status: str
    expiresAt: str | None
    paidAt: str | None
    appliedAt: str | None
    failureReason: str | None
    createdAt: str
    billing: InvoiceBilling
    plan: InvoicePlanSummary | None


class InvoiceDetail(InvoiceListItem, total=False):
    """Checkout / status — PIX fields only when asked or on create."""

    brCode: str | None
    brCodeBase64: str | None


class InvoicesListResponse(TypedDict):
    success: bool
    invoices: list[InvoiceListItem]


class InvoiceDetailResponse(TypedDict):
    success: bool
    invoice: InvoiceDetail


class CreatePixInvoiceInput(TypedDict, total=False):
    planId: str
    interval: str


# ── Plans ───────────────────────────────────────────────────────────────────


class PlanPriceInfo(TypedDict):
    id: str
    interval: str
    months: int
    discountPercent: float
    priceCents: int


class PlanInfo(TypedDict, total=False):
    id: str
    name: str
    price: float
    ramMB: int
    vcpu: int
    totalRAM: int
    totalVCPU: int
    estimatedProjects: int
    prices: list[PlanPriceInfo]


class PlanUsage(TypedDict):
    usedRAM: float
    availableRAM: float
    ramPercentage: float
    totalApps: int
    totalDatabases: int


class CurrentPlanBilling(TypedDict):
    interval: str
    months: int
    planExpiresAt: str | None
    downgradedToFree: bool


class CurrentPlanResponse(TypedDict):
    success: bool
    plan: PlanInfo
    usage: PlanUsage
    billing: CurrentPlanBilling


class PlansListResponse(TypedDict):
    success: bool
    plans: list[PlanInfo]


# ── GitHub integration ──────────────────────────────────────────────────────


class GithubStatusResponse(TypedDict, total=False):
    success: bool
    connected: bool
    hasRequiredScope: bool
    missingScopes: list[str]
    provider: str | None
    installationId: str
    accountLogin: str
    appConfigured: bool
