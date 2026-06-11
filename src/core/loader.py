import httpx


def load_spec(swagger_url: str) -> dict:
    response = httpx.get(swagger_url)
    response.raise_for_status()
    return response.json()
