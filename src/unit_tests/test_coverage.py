import pytest
from unittest.mock import AsyncMock, Mock

from models import Endpoint, ParsedSpec
from services.coverage import CoverageService


ENDPOINT_GET_USERS = Endpoint(method="GET", path="/users", tags=("api",))
ENDPOINT_POST_USERS = Endpoint(method="POST", path="/users", tags=("api",))

SAMPLE_SPEC = ParsedSpec(
    all_endpoints=frozenset([ENDPOINT_GET_USERS, ENDPOINT_POST_USERS]),
    by_tag={
        "api": [ENDPOINT_GET_USERS, ENDPOINT_POST_USERS],
    },
)

SWAGGER_URL = "http://example.com/swagger.json"
RAW_SPEC = {"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}}


@pytest.fixture
def mock_loader():
    return AsyncMock()


@pytest.fixture
def mock_parser():
    return Mock()


@pytest.fixture
def mock_matcher():
    return Mock()


@pytest.fixture
def svc(mock_loader, mock_parser, mock_matcher):
    return CoverageService(
        loader=mock_loader,
        parser=mock_parser,
        matcher=mock_matcher,
    )


class TestInitialize:
    @pytest.mark.asyncio
    async def test_returns_true(self, svc, mock_loader, mock_parser):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC

        result = await svc.initialize(SWAGGER_URL)

        assert result is True

    @pytest.mark.asyncio
    async def test_sets_spec(self, svc, mock_loader, mock_parser):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC

        await svc.initialize(SWAGGER_URL)

        assert svc.spec is SAMPLE_SPEC

    @pytest.mark.asyncio
    async def test_sets_swagger_url(self, svc, mock_loader, mock_parser):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC

        await svc.initialize(SWAGGER_URL)

        assert svc.swagger_url == SWAGGER_URL

    @pytest.mark.asyncio
    async def test_sets_is_initialized(self, svc, mock_loader, mock_parser):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC

        await svc.initialize(SWAGGER_URL)

        assert svc.is_initialized is True

    @pytest.mark.asyncio
    async def test_clears_covered_on_reinit(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.mark("GET", "/users")

        await svc.initialize(SWAGGER_URL)

        assert svc.covered_count == 0

    @pytest.mark.asyncio
    async def test_clears_history_on_reinit(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.record_request("GET", "/users", 200, 10.0)

        await svc.initialize(SWAGGER_URL)

        assert svc.get_history("GET", "/users") == []

    @pytest.mark.asyncio
    async def test_returns_false_when_loader_fails(self, svc, mock_loader):
        mock_loader.return_value = None

        result = await svc.initialize(SWAGGER_URL)

        assert result is False

    @pytest.mark.asyncio
    async def test_spec_stays_none_when_loader_fails(self, svc, mock_loader):
        mock_loader.return_value = None

        await svc.initialize(SWAGGER_URL)

        assert svc.spec is None

    @pytest.mark.asyncio
    async def test_is_initialized_false_when_loader_fails(self, svc, mock_loader):
        mock_loader.return_value = None

        await svc.initialize(SWAGGER_URL)

        assert svc.is_initialized is False


class TestMark:
    @pytest.mark.asyncio
    async def test_adds_matched_endpoint(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.mark("GET", "/users")

        assert ENDPOINT_GET_USERS in svc.covered

    @pytest.mark.asyncio
    async def test_increments_covered_count(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.mark("GET", "/users")

        assert svc.covered_count == 1

    @pytest.mark.asyncio
    async def test_does_not_add_unmatched(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = None
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.mark("GET", "/unknown")

        assert svc.covered_count == 0

    @pytest.mark.asyncio
    async def test_does_not_duplicate(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.mark("GET", "/users")
        svc.mark("GET", "/users")

        assert svc.covered_count == 1

    def test_noop_without_spec(self, svc):
        svc.mark("GET", "/users")

        assert svc.covered_count == 0


class TestRecordRequest:
    @pytest.mark.asyncio
    async def test_adds_record(self, svc, mock_loader, mock_parser, mock_matcher):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.record_request("GET", "/users", 200, 15.5)

        records = svc.get_history("GET", "/users")
        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_records_method_and_path(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.record_request("GET", "/users", 200, 15.5)

        record = svc.get_history("GET", "/users")[0]
        assert record.method == "GET"
        assert record.path == "/users"

    @pytest.mark.asyncio
    async def test_records_status_and_duration(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.record_request("GET", "/users", 200, 15.5)

        record = svc.get_history("GET", "/users")[0]
        assert record.status_code == 200
        assert record.duration_ms == 15.5

    @pytest.mark.asyncio
    async def test_records_optional_fields(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.record_request("GET", "/users", 200, 15.5, query_params="page=1")

        record = svc.get_history("GET", "/users")[0]
        assert record.query_params == "page=1"

    @pytest.mark.asyncio
    async def test_does_not_add_unmatched(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = None
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        svc.record_request("GET", "/unknown", 404, 5.0)

        assert svc.get_history("GET", "/unknown") == []

    def test_noop_without_spec(self, svc):
        svc.record_request("GET", "/users", 200, 10.0)

        assert svc.get_history("GET", "/users") == []


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_returns_records_for_known_key(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.record_request("GET", "/users", 200, 10.0)

        records = svc.get_history("GET", "/users")

        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_unknown_key(
        self, svc, mock_loader, mock_parser
    ):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        records = svc.get_history("GET", "/unknown")

        assert records == []

    @pytest.mark.asyncio
    async def test_returns_copy_not_original(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.record_request("GET", "/users", 200, 10.0)

        records = svc.get_history("GET", "/users")
        records.append("should_not_affect_service")

        assert len(svc.get_history("GET", "/users")) == 1


class TestClear:
    @pytest.mark.asyncio
    async def test_clears_covered(self, svc, mock_loader, mock_parser, mock_matcher):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.mark("GET", "/users")

        svc.clear()

        assert svc.covered_count == 0

    @pytest.mark.asyncio
    async def test_clears_history(self, svc, mock_loader, mock_parser, mock_matcher):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.record_request("GET", "/users", 200, 10.0)

        svc.clear()

        assert svc.get_history("GET", "/users") == []


class TestRatio:
    def test_zero_when_no_spec(self, svc):
        assert svc.ratio == 0.0

    @pytest.mark.asyncio
    async def test_zero_when_nothing_covered(self, svc, mock_loader, mock_parser):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        assert svc.ratio == 0.0

    @pytest.mark.asyncio
    async def test_half_when_one_of_two_covered(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.return_value = ENDPOINT_GET_USERS
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.mark("GET", "/users")

        assert svc.ratio == 0.5

    @pytest.mark.asyncio
    async def test_one_when_all_covered(
        self, svc, mock_loader, mock_parser, mock_matcher
    ):
        mock_matcher.side_effect = [ENDPOINT_GET_USERS, ENDPOINT_POST_USERS]
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)
        svc.mark("GET", "/users")
        svc.mark("POST", "/users")

        assert svc.ratio == 1.0


class TestProperties:
    def test_is_initialized_false_by_default(self, svc):
        assert svc.is_initialized is False

    def test_covered_count_zero_without_spec(self, svc):
        assert svc.covered_count == 0

    def test_total_count_zero_without_spec(self, svc):
        assert svc.total_count == 0

    @pytest.mark.asyncio
    async def test_total_count_after_init(self, svc, mock_loader, mock_parser):
        mock_loader.return_value = RAW_SPEC
        mock_parser.return_value = SAMPLE_SPEC
        await svc.initialize(SWAGGER_URL)

        assert svc.total_count == 2

    def test_swagger_url_empty_by_default(self, svc):
        assert svc.swagger_url == ""
