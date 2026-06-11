from src.core.parser import get_endpoints_by_tags, get_endpoints

sample_spec = {
    "swagger": "2.0",
    "paths": {
        "/pet/{petId}/uploadImage": {
            "post": {"tags": ["pet"], "summary": "uploads an image"}
        },
        "/pet": {
            "post": {"tags": ["pet"], "summary": "Add a new pet"},
            "put": {"tags": ["pet"], "summary": "Update an existing pet"},
        },
        "/pet/findByStatus": {
            "get": {"tags": ["pet"], "summary": "Finds pets by status"}
        },
        "/store/inventory": {
            "get": {
                "tags": ["store"],
                "summary": "Returns pet inventories by status",
            }
        },
        "/user/{username}": {
            "get": {"tags": ["user"], "summary": "Get user by username"}
        },
        "/untagged/endpoint": {"get": {"summary": "Endpoint without tags"}},
    },
}


def test_get_endpoints():
    result = get_endpoints(sample_spec)

    expected = [
        {"method": "POST", "path": "/pet/{petId}/uploadImage"},
        {"method": "POST", "path": "/pet"},
        {"method": "PUT", "path": "/pet"},
        {"method": "GET", "path": "/pet/findByStatus"},
        {"method": "GET", "path": "/store/inventory"},
        {"method": "GET", "path": "/user/{username}"},
        {"method": "GET", "path": "/untagged/endpoint"},
    ]

    assert len(result) == len(expected)
    for item in expected:
        assert item in result


def test_get_endpoints_by_tags():
    result = get_endpoints_by_tags(sample_spec)

    expected = {
        "pet": [
            {"method": "POST", "path": "/pet/{petId}/uploadImage"},
            {"method": "POST", "path": "/pet"},
            {"method": "PUT", "path": "/pet"},
            {"method": "GET", "path": "/pet/findByStatus"},
        ],
        "store": [{"method": "GET", "path": "/store/inventory"}],
        "user": [{"method": "GET", "path": "/user/{username}"}],
        "default": [{"method": "GET", "path": "/untagged/endpoint"}],
    }

    assert set(result.keys()) == set(expected.keys())
    for tag in expected:
        assert len(result[tag]) == len(expected[tag])
        for endpoint in expected[tag]:
            assert endpoint in result[tag]


def test_empty_spec():
    empty_spec = {"swagger": "2.0", "paths": {}}

    assert get_endpoints(empty_spec) == []
    assert get_endpoints_by_tags(empty_spec) == {}
