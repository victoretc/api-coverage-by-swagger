import httpx


async def load_spec(swagger_url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(swagger_url)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError):
        return None
