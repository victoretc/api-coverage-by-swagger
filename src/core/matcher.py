import re
from functools import lru_cache

from models import Endpoint


@lru_cache(maxsize=None)
def _compile_regex(path: str) -> re.Pattern:
    if not path.startswith("/"):
        path = "/" + path
    parts = path.split("/")
    regex_parts = []

    for part in parts[1:]:
        if part.startswith("{") and part.endswith("}"):
            regex_parts.append("[^/]+")
        else:
            regex_parts.append(re.escape(part))

    return re.compile(f"^/{'/'.join(regex_parts)}$")


def match_endpoint(
    method: str,
    path: str,
    candidates: frozenset[Endpoint],
) -> Endpoint | None:
    parsed = path.removeprefix("/proxy").split("?")[0]
    method = method.upper()

    for ep in candidates:
        if ep.method == method and _compile_regex(ep.path).fullmatch(parsed):
            return ep
    return None
