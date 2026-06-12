from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    tags: tuple[str, ...] = ("default",)


@dataclass
class ParsedSpec:
    all_endpoints: frozenset[Endpoint]
    by_tag: dict[str, list[Endpoint]]


@dataclass
class RequestRecord:
    method: str
    path: str
    status_code: int
    timestamp: str
    duration_ms: float
    query_params: str | None = None
    content_type: str | None = None
    request_preview: str | None = None
    response_preview: str | None = None
