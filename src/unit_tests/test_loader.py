from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from core.loader import load_spec


@pytest.fixture(autouse=True)
def _mock_httpx():
    with patch("httpx.AsyncClient") as mock:
        mock_client = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_client
        mock_response = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_response.raise_for_status = Mock()
        yield mock_response


class TestLoadSpec:
    @pytest.mark.asyncio
    async def test_returns_json_dict(self, _mock_httpx):
        _mock_httpx.text = '{"key": "value"}'

        result = await load_spec("http://example.com/swagger.json")

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_falls_back_to_yaml_when_not_json(self, _mock_httpx):
        yaml_text = (
            "openapi: 3.0.3\ninfo:\n  title: Test\n  version: '1.0'\npaths: {}\n"
        )
        _mock_httpx.text = yaml_text
        with patch(
            "core.loader.prance_parse_spec", return_value={"parsed": "spec"}
        ) as mock_prance:
            result = await load_spec("http://example.com/spec.yaml")

        mock_prance.assert_called_once_with(
            yaml_text, url="http://example.com/spec.yaml"
        )
        assert result == {"parsed": "spec"}

    @pytest.mark.asyncio
    async def test_returns_none_when_prance_returns_non_dict(self, _mock_httpx):
        _mock_httpx.text = "not json or yaml"
        with patch("core.loader.prance_parse_spec", return_value="not a dict"):
            result = await load_spec("http://example.com/spec.yaml")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_http_error(self, _mock_httpx):
        _mock_httpx.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=Mock(), response=Mock()
        )

        result = await load_spec("http://example.com/swagger.json")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_network_error(self, _mock_httpx):
        _mock_httpx.raise_for_status.side_effect = httpx.RequestError(
            "Connection failed", request=Mock()
        )

        result = await load_spec("http://example.com/swagger.json")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_value_error(self, _mock_httpx):
        _mock_httpx.raise_for_status.side_effect = ValueError("bad value")

        result = await load_spec("http://example.com/swagger.json")

        assert result is None
