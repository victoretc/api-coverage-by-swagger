import json

import httpx
from prance.util.formats import parse_spec as prance_parse_spec


async def load_spec(swagger_url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(swagger_url)
            response.raise_for_status()
            text = response.text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                result = prance_parse_spec(text, url=swagger_url)
                if isinstance(result, dict):
                    return result
                return None
    except (httpx.HTTPStatusError, httpx.RequestError, ValueError):
        return None
