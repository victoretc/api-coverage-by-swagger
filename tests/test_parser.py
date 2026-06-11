from core.parser import parse_spec
from models import Endpoint

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

expected_endpoints = frozenset(
    [
        Endpoint(method="POST", path="/pet/{petId}/uploadImage", tags=("pet",)),
        Endpoint(method="POST", path="/pet", tags=("pet",)),
        Endpoint(method="PUT", path="/pet", tags=("pet",)),
        Endpoint(method="GET", path="/pet/findByStatus", tags=("pet",)),
        Endpoint(method="GET", path="/store/inventory", tags=("store",)),
        Endpoint(method="GET", path="/user/{username}", tags=("user",)),
        Endpoint(method="GET", path="/untagged/endpoint", tags=("default",)),
    ]
)


def test_parse_spec_all_endpoints():
    result = parse_spec(sample_spec)
    assert len(result.all_endpoints) == len(expected_endpoints)
    for ep in expected_endpoints:
        assert ep in result.all_endpoints


def test_parse_spec_by_tag():
    result = parse_spec(sample_spec)

    assert set(result.by_tag) == {"pet", "store", "user", "default"}

    assert len(result.by_tag["pet"]) == 4
    for ep in (
        Endpoint(method="POST", path="/pet/{petId}/uploadImage", tags=("pet",)),
        Endpoint(method="POST", path="/pet", tags=("pet",)),
        Endpoint(method="PUT", path="/pet", tags=("pet",)),
        Endpoint(method="GET", path="/pet/findByStatus", tags=("pet",)),
    ):
        assert ep in result.by_tag["pet"]

    assert len(result.by_tag["store"]) == 1
    assert (
        Endpoint(method="GET", path="/store/inventory", tags=("store",))
        in result.by_tag["store"]
    )

    assert len(result.by_tag["user"]) == 1
    assert (
        Endpoint(method="GET", path="/user/{username}", tags=("user",))
        in result.by_tag["user"]
    )

    assert len(result.by_tag["default"]) == 1
    assert (
        Endpoint(method="GET", path="/untagged/endpoint", tags=("default",))
        in result.by_tag["default"]
    )


def test_empty_spec():
    empty_spec = {"swagger": "2.0", "paths": {}}
    result = parse_spec(empty_spec)
    assert result.all_endpoints == frozenset()
    assert result.by_tag == {}
