import re
from urllib.parse import urlparse


def swagger_path_to_regex(path: str) -> re.Pattern:
    if not path.startswith("/"):
        path = "/" + path

    parts = path.split("/")
    regex_parts = []

    for part in parts[1:]:
        if part.startswith("{") and part.endswith("}"):
            param_name = part[1:-1]
            regex_parts.append(f"(?P<{param_name}>[^/]+)")
        else:
            regex_parts.append(re.escape(part))

    return re.compile("^/" + "/".join(regex_parts) + "$")


def match_endpoint(method: str, path: str, raw_endpoints: list[dict]) -> dict | None:
    parsed_url = urlparse(path)
    parsed_path = parsed_url.path.replace("/proxy", "").split("?")[0]

    for endpoint in raw_endpoints:
        if endpoint["method"] == method.upper() and swagger_path_to_regex(
            endpoint["path"]
        ).fullmatch(parsed_path):
            return endpoint
    return None
