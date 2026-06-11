import pytest
from src.core.utils import swagger_path_to_regex, match_endpoint


sample_endpoints = [
    {"method": "GET", "path": "/pet/{petId}"},
    {"method": "POST", "path": "/pet/{petId}/uploadImage"},
    {"method": "GET", "path": "/store/order/{orderId}"},
    {"method": "GET", "path": "/user/{username}"},
    {"method": "GET", "path": "/static/path"},
]


class TestSwaggerPathToRegex:
    @pytest.mark.parametrize(
        "path,expected_pattern",
        [
            ("/pet/{petId}", r"^/pet/(?P<petId>[^/]+)$"),
            ("/user/{username}", r"^/user/(?P<username>[^/]+)$"),
            ("/static/path", r"^/static/path$"),
            ("pet/{petId}", r"^/pet/(?P<petId>[^/]+)$"),
            (
                "/store/order/{orderId}/items",
                r"^/store/order/(?P<orderId>[^/]+)/items$",
            ),
        ],
    )
    def test_path_conversion(self, path, expected_pattern):
        pattern = swagger_path_to_regex(path)
        assert pattern.pattern == expected_pattern

    def test_compile_regex(self):
        pattern = swagger_path_to_regex("/pet/{petId}")
        assert pattern.fullmatch("/pet/123")
        assert not pattern.fullmatch("/pet/123/extra")
        assert not pattern.fullmatch("/pet/")


class TestMatchEndpoint:
    @pytest.mark.parametrize(
        "method,path,expected",
        [
            ("GET", "/pet/123", {"method": "GET", "path": "/pet/{petId}"}),
            (
                "POST",
                "/pet/456/uploadImage",
                {"method": "POST", "path": "/pet/{petId}/uploadImage"},
            ),
            ("GET", "/user/john_doe", {"method": "GET", "path": "/user/{username}"}),
            ("GET", "/static/path", {"method": "GET", "path": "/static/path"}),
            (
                "GET",
                "/store/order/789",
                {"method": "GET", "path": "/store/order/{orderId}"},
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
        assert result == {"method": "GET", "path": "/user/{username}"}

    def test_url_with_proxy_prefix(self):
        result = match_endpoint("GET", "/proxy/user/john", sample_endpoints)
        assert result == {"method": "GET", "path": "/user/{username}"}

    def test_empty_endpoints(self):
        assert match_endpoint("GET", "/any/path", []) is None
