import logging

from collections.abc import Awaitable, Callable

from core.matcher import EndpointMatcher
from models import CoverageState, ParsedSpec

logger = logging.getLogger(__name__)


class CoverageService:
    def __init__(
        self,
        *,
        loader: Callable[[str], Awaitable[dict | None]],
        parser: Callable[[dict], ParsedSpec],
        matcher: EndpointMatcher | None = None,
    ):
        self._loader = loader
        self._parser = parser
        self._matcher = matcher or EndpointMatcher()
        self._state: CoverageState | None = None

    @property
    def is_initialized(self) -> bool:
        return self._state is not None

    @property
    def state(self) -> CoverageState | None:
        return self._state

    async def initialize(self, swagger_url: str) -> bool:
        raw = await self._loader(swagger_url)
        if raw is None:
            return False
        self._state = CoverageState(
            spec=self._parser(raw),
            swagger_url=swagger_url,
        )
        return True

    def mark(self, method: str, path: str) -> None:
        if self._state is None:
            return
        ep = self._matcher.match(method, path, self._state.spec.all_endpoints)
        if ep is not None and ep not in self._state.covered:
            self._state.covered.add(ep)
            logger.info("Covered %s %s", ep.method, ep.path)

    def clear(self) -> None:
        if self._state is not None:
            self._state.covered.clear()
