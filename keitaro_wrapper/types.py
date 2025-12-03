from typing import TypedDict, Literal, Any, TypeAlias


class Offer(TypedDict):
    id: int
    name: str
    group_id: int
    action_type: str
    action_payload: str
    action_options: dict[str, str]
    affiliate_network_id: int
    payout_value: float | int
    payout_currency: str
    payout_type: str
    state: str
    created_at: str
    updated_at: str
    payout_auto: bool
    payout_upsell: bool
    country: list[str]
    notes: str
    affiliate_network: str
    archive: str
    local_path: str
    preview_path: str
    values: list[dict[str, str]]


class Domain(TypedDict):
    id: int
    name: str
    network_status: str
    default_campaign: str
    default_campaign_id: int
    state: str
    created_at: str
    updated_at: str
    catch_not_found: bool
    campaigns_count: int
    ssl_redirect: bool
    allow_indexing: bool
    admin_dashboard: bool
    cloudflare_proxy: bool
    group_id: int
    group: str
    is_ssl: bool
    dns_provider: str
    error_solution: str
    status: str
    notes: str


class SourceParameter(TypedDict):
    name: str
    placeholder: str
    alias: str


class Source(TypedDict):
    id: int
    name: str
    postback_url: str
    postback_statuses: list[str]
    template_name: str
    accept_parameters: bool
    parameters: dict[str, SourceParameter]
    notes: str
    state: str
    created_at: str
    updated_at: str
    traffic_loss: int
    update_in_campaigns: str


class Group(TypedDict):
    id: int
    name: str
    position: int
    type: str


class CampaignPayload(TypedDict, total=False):
    alias: str
    name: str
    type: Literal["position", "weight"]
    cookies_ttl: int
    state: Literal["active", "disabled", "deleted"]
    cost_type: Literal["CPC", "CPUC", "CPM"]
    cost_value: float
    cost_currency: str
    cost_auto: bool
    group_id: int
    bind_visitors: Literal["s", "sl", "slo"]
    traffic_source_id: int
    domain_id: int
    notes: str
    parameters: dict[str, SourceParameter]
    token: str
    postbacks: list[dict[str, str | int | list[str]]]


class FlowFilter(TypedDict, total=False):
    name: str
    mode: Literal["accept", "reject"]
    payload: list[str]
    id: int


class FlowOffer(TypedDict, total=False):
    offer_id: int
    share: int
    state: Literal["active", "disabled"]


class FlowAction(TypedDict, total=False):
    key: str
    name: str
    field: str
    type: str
    description: str


class FlowPayload(TypedDict, total=False):
    campaign_id: int
    schema: Literal["landings", "redirect", "action"]
    type: Literal["forced", "regular", "default"]
    name: str
    action_type: str
    position: int
    weight: float
    action_options: dict[str, Any]
    comments: str
    state: Literal["active", "disabled", "deleted"]
    collect_clicks: bool
    filter_or: bool
    filters: list[FlowFilter]
    offers: list[FlowOffer]
    landings: list[dict[str, Any]]


class Campaign(TypedDict):
    id: int
    alias: str
    name: str
    type: str
    uniqueness_method: str
    cookies_ttl: int
    position: int
    state: str
    updated_at: str
    cost_type: str
    cost_value: int
    cost_currency: str
    group_id: int
    bind_visitors: str
    traffic_source_id: int
    token: str
    cost_auto: bool
    domain_id: int | None
    notes: str | None
    parameters: list
    uniqueness_use_cookies: bool
    traffic_loss: int
    bypass_cache: bool
    created_at: str
    domain: str | None
    postbacks: list
    group: str


class CampaignFlowOffer(TypedDict):
    id: int
    stream_id: int
    offer_id: int
    state: str
    share: int
    created_at: str
    updated_at: str


class Flow(TypedDict):
    id: int
    type: str
    name: str
    campaign_id: int
    position: int
    action_options: dict | None
    comments: str | None
    state: str
    action_type: str
    action_payload: str | None
    schema: str
    collect_clicks: bool
    filter_or: bool
    weight: int
    offer_selection: str
    filters: list
    triggers: list
    landings: list
    offers: list[CampaignFlowOffer]


APIResponse: TypeAlias = (
      list[Offer]
    | list[Domain]
    | list[Source]
    | list[Group]
    | list[FlowAction]
    | list[Campaign]
    | list[Flow]
    | Campaign
)