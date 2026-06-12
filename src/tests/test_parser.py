import json

import pytest
from prance.util.formats import parse_spec as prance_parse_spec

from core.parser import parse_spec
from models import Endpoint, ParsedSpec

swagger_sample = {
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

openapi_sample = {
    "openapi": "3.0.3",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/pet/{petId}/uploadImage": {
            "post": {
                "tags": ["pet"],
                "summary": "uploads an image",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/pet": {
            "post": {
                "tags": ["pet"],
                "summary": "Add a new pet",
                "responses": {"200": {"description": "OK"}},
            },
            "put": {
                "tags": ["pet"],
                "summary": "Update an existing pet",
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/pet/findByStatus": {
            "get": {
                "tags": ["pet"],
                "summary": "Finds pets by status",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/store/inventory": {
            "get": {
                "tags": ["store"],
                "summary": "Returns pet inventories by status",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/user/{username}": {
            "get": {
                "tags": ["user"],
                "summary": "Get user by username",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/untagged/endpoint": {
            "get": {
                "summary": "Endpoint without tags",
                "responses": {"200": {"description": "OK"}},
            }
        },
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


@pytest.mark.parametrize(
    "spec",
    [
        pytest.param(swagger_sample, id="swagger-2.0"),
        pytest.param(openapi_sample, id="openapi-3.0"),
    ],
)
class TestParseSpec:
    def test_all_endpoints(self, spec):
        result = parse_spec(spec)
        assert len(result.all_endpoints) == len(expected_endpoints)
        for ep in expected_endpoints:
            assert ep in result.all_endpoints

    def test_by_tag(self, spec):
        result = parse_spec(spec)

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


def test_swagger_empty_paths():
    assert parse_spec({"swagger": "2.0", "paths": {}}) == ParsedSpec(
        all_endpoints=frozenset(), by_tag={}
    )


def test_openapi_empty_paths():
    assert parse_spec({"openapi": "3.0.0", "info": {}, "paths": {}}) == ParsedSpec(
        all_endpoints=frozenset(), by_tag={}
    )


def test_yaml_spec():
    yaml_text = """openapi: 3.0.3
info:
  title: Test API
  version: "1.0"
paths:
  /items:
    get:
      tags: [store]
      responses:
        "200":
          description: OK
  /items/{id}:
    get:
      tags: [store]
      responses:
        "200":
          description: OK
"""
    parsed = prance_parse_spec(yaml_text, url="file:///spec.yaml")
    result = parse_spec(parsed)
    assert len(result.all_endpoints) == 2
    assert (
        Endpoint(method="GET", path="/items", tags=("store",)) in result.all_endpoints
    )
    assert (
        Endpoint(method="GET", path="/items/{id}", tags=("store",))
        in result.all_endpoints
    )


def test_yaml_json_equivalent():
    yaml_text = """openapi: 3.0.3
info:
  title: Test
  version: "1.0"
paths:
  /foo:
    get:
      tags: [demo]
      responses:
        "200":
          description: OK
"""
    yaml_parsed = prance_parse_spec(yaml_text, url="file:///spec.yaml")
    json_parsed = json.loads(json.dumps(yaml_parsed))
    assert (
        parse_spec(yaml_parsed).all_endpoints == parse_spec(json_parsed).all_endpoints
    )


def test_path_ref_resolution():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/pets": {"$ref": "#/components/pathItems/myPets"},
        },
        "components": {
            "pathItems": {
                "myPets": {
                    "get": {
                        "tags": ["pet"],
                        "responses": {"200": {"description": "OK"}},
                    },
                    "post": {
                        "tags": ["pet"],
                        "responses": {"201": {"description": "Created"}},
                    },
                }
            }
        },
    }
    result = parse_spec(spec)
    assert len(result.all_endpoints) == 2
    assert Endpoint(method="GET", path="/pets", tags=("pet",)) in result.all_endpoints
    assert Endpoint(method="POST", path="/pets", tags=("pet",)) in result.all_endpoints


def test_path_item_with_ref_in_operation():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/items": {
                "post": {
                    "tags": ["items"],
                    "requestBody": {"$ref": "#/components/requestBodies/ItemBody"},
                    "responses": {"201": {"description": "Created"}},
                }
            }
        },
        "components": {
            "requestBodies": {
                "ItemBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    }
                }
            },
            "schemas": {
                "Item": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        },
    }
    result = parse_spec(spec)
    assert len(result.all_endpoints) == 1
    assert (
        Endpoint(method="POST", path="/items", tags=("items",)) in result.all_endpoints
    )


def test_servers_url_does_not_affect_parsing():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "servers": [{"url": "https://api.example.com/v1"}],
        "paths": {
            "/users": {
                "get": {
                    "tags": ["users"],
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    result = parse_spec(spec)
    assert len(result.all_endpoints) == 1
    assert (
        Endpoint(method="GET", path="/users", tags=("users",)) in result.all_endpoints
    )
