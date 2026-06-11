from dataclasses import dataclass, field
from .loader import load_spec
from .parser import get_endpoints, get_endpoints_by_tags
from .utils import match_endpoint


@dataclass
class CoverageService:
    _current_swagger_url: str = None
    _covered_endpoints: set[tuple[str, str]] = field(default_factory=set)
    _raw_endpoints: list[dict] = field(default_factory=list)
    _global_spec: dict = None

    @property
    def is_initialized(self) -> bool:
        return self._global_spec is not None

    def initialize(self, swagger_url: str) -> bool:
        spec = load_spec(swagger_url)
        if not spec:
            return False

        self._raw_endpoints = get_endpoints(spec)
        self._global_spec = spec
        self._current_swagger_url = swagger_url
        return True

    def mark_covered(self, method: str, path: str) -> None:
        endpoint = match_endpoint(method, path, self._raw_endpoints)
        if endpoint:
            self._covered_endpoints.add((endpoint["method"], endpoint["path"]))

    def clear_coverage(self) -> None:
        self._covered_endpoints.clear()

    def get_coverage_data(self) -> dict:
        coverage_percentage = self._calculate_coverage()
        endpoints_by_tags = get_endpoints_by_tags(self._global_spec)

        return {
            "total_endpoints": len(self._raw_endpoints),
            "covered_endpoints_count": len(self._covered_endpoints),
            "coverage_percentage": coverage_percentage,
            "endpoints_by_tags": endpoints_by_tags,
            "tags": list(endpoints_by_tags.keys()),
            "covered_endpoints": self._covered_endpoints,
        }

    def _calculate_coverage(self) -> float:
        if not self._raw_endpoints:
            return 0.0
        return round((len(self._covered_endpoints) / len(self._raw_endpoints)) * 100, 2)
