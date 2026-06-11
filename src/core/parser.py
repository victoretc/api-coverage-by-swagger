def get_endpoints_by_tags(spec: dict) -> dict[str, list[dict]]:
    tags = {}
    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if isinstance(details, dict):
                endpoint = {"method": method.upper(), "path": path}
                for tag in details.get("tags", ["default"]):
                    tags.setdefault(tag, []).append(endpoint)
    return tags


def get_endpoints(spec: dict) -> list[dict]:
    return [
        {"method": method.upper(), "path": path}
        for path, methods in spec["paths"].items()
        for method, _ in methods.items()
    ]
