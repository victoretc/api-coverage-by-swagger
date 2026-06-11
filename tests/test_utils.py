import pytest

from core.matcher import match_endpoint
from models import Endpoint

sample_endpoints = frozenset(
    [
        Endpoint(method="GET", path="/pet/{petId}"),
        Endpoint(method="POST", path="/pet/{petId}/uploadImage"),
        Endpoint(method="GET", path="/store/order/{orderId}"),
        Endpoint(method="GET", path="/user/{username}"),
        Endpoint(method="GET", path="/static/path"),
    ]
)


class TestMatchEndpoint:
    @pytest.mark.parametrize(
        "method,path,expected",
        [
            ("GET", "/pet/123", Endpoint(method="GET", path="/pet/{petId}")),
            (
                "POST",
                "/pet/456/uploadImage",
                Endpoint(method="POST", path="/pet/{petId}/uploadImage"),
            ),
            (
                "GET",
                "/user/john_doe",
                Endpoint(method="GET", path="/user/{username}"),
            ),
            ("GET", "/static/path", Endpoint(method="GET", path="/static/path")),
            (
                "GET",
                "/store/order/789",
                Endpoint(method="GET", path="/store/order/{orderId}"),
            ),
        ],
    )
    def test_matching_paths(self, method, path, expected):
        result = match_endpoint(method, path, sample_endpoints)
        assert result == expected

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/pet/123/extra"),
            ("PUT", "/pet/123"),
            ("GET", "/nonexistent"),
            ("GET", "/pet/"),
        ],
    )
    def test_non_matching_paths(self, method, path):
        assert match_endpoint(method, path, sample_endpoints) is None

    def test_url_with_query_params(self):
        result = match_endpoint("GET", "/user/john?param=value", sample_endpoints)
        assert result == Endpoint(method="GET", path="/user/{username}")

    def test_url_with_proxy_prefix(self):
        result = match_endpoint("GET", "/proxy/user/john", sample_endpoints)
        assert result == Endpoint(method="GET", path="/user/{username}")

    def test_empty_endpoints(self):
        assert match_endpoint("GET", "/any/path", frozenset()) is None
