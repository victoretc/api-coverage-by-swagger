import logging

from collections.abc import Awaitable, Callable

from core.matcher import match_endpoint
from models import Endpoint, ParsedSpec

logger = logging.getLogger(__name__)


class CoverageService:
    def __init__(
        self,
        *,
        loader: Callable[[str], Awaitable[dict | None]],
        parser: Callable[[dict], ParsedSpec],
        matcher: Callable[[str, str, frozenset[Endpoint]], Endpoint | None] = match_endpoint,
    ):
        self._loader = loader
        self._parser = parser
        self._matcher = matcher
        self._spec: ParsedSpec | None = None
        self._swagger_url: str = ""
        self._covered: set[Endpoint] = set()

    @property
    def is_initialized(self) -> bool:
        return self._spec is not None

    @property
    def spec(self) -> ParsedSpec | None:
        return self._spec

    @property
    def covered(self) -> set[Endpoint]:
        return self._covered

    @property
    def swagger_url(self) -> str:
        return self._swagger_url

    @property
    def ratio(self) -> float:
        if not self._spec or not self._spec.all_endpoints:
            return 0.0
        return len(self._covered) / len(self._spec.all_endpoints)

    @property
    def covered_count(self) -> int:
        return len(self._covered)

    @property
    def total_count(self) -> int:
        return len(self._spec.all_endpoints) if self._spec else 0

    async def initialize(self, swagger_url: str) -> bool:
        raw = await self._loader(swagger_url)
        if raw is None:
            return False
        self._spec = self._parser(raw)
        self._swagger_url = swagger_url
        self._covered = set()
        return True

    def mark(self, method: str, path: str) -> None:
        if self._spec is None:
            return
        ep = self._matcher(method, path, self._spec.all_endpoints)
        if ep is not None and ep not in self._covered:
            self._covered.add(ep)
            logger.info("Covered %s %s", ep.method, ep.path)

    def clear(self) -> None:
        self._covered.clear()
