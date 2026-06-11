import pytest

from core.matcher import _compile_regex, EndpointMatcher
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


class TestSwaggerPathToRegex:
    @pytest.mark.parametrize(
        "path,expected_pattern",
        [
            ("/pet/{petId}", r"^/pet/[^/]+$"),
            ("/user/{username}", r"^/user/[^/]+$"),
            ("/static/path", r"^/static/path$"),
            ("pet/{petId}", r"^/pet/[^/]+$"),
            (
                "/store/order/{orderId}/items",
                r"^/store/order/[^/]+/items$",
            ),
        ],
    )
    def test_path_conversion(self, path, expected_pattern):
        pattern = _compile_regex(path)
        assert pattern.pattern == expected_pattern

    def test_compile_regex(self):
        pattern = _compile_regex("/pet/{petId}")
        assert pattern.fullmatch("/pet/123")
        assert not pattern.fullmatch("/pet/123/extra")
        assert not pattern.fullmatch("/pet/")


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
        matcher = EndpointMatcher()
        result = matcher.match(method, path, sample_endpoints)
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
        matcher = EndpointMatcher()
        assert matcher.match(method, path, sample_endpoints) is None

    def test_url_with_query_params(self):
        matcher = EndpointMatcher()
        result = matcher.match("GET", "/user/john?param=value", sample_endpoints)
        assert result == Endpoint(method="GET", path="/user/{username}")

    def test_url_with_proxy_prefix(self):
        matcher = EndpointMatcher()
        result = matcher.match("GET", "/proxy/user/john", sample_endpoints)
        assert result == Endpoint(method="GET", path="/user/{username}")

    def test_empty_endpoints(self):
        matcher = EndpointMatcher()
        assert matcher.match("GET", "/any/path", frozenset()) is None
