from dataclasses import dataclass, field


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
class CoverageState:
    spec: ParsedSpec
    swagger_url: str = ""
    covered: set[Endpoint] = field(default_factory=set)

    @property
    def ratio(self) -> float:
        if not self.spec.all_endpoints:
            return 0.0
        return len(self.covered) / len(self.spec.all_endpoints)

    @property
    def covered_count(self) -> int:
        return len(self.covered)

    @property
    def total_count(self) -> int:
        return len(self.spec.all_endpoints)
