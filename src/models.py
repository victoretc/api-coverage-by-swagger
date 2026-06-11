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
