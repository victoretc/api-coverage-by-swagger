from models import Endpoint, ParsedSpec


def parse_spec(spec: dict) -> ParsedSpec:
    endpoints: set[Endpoint] = set()
    by_tag: dict[str, list[Endpoint]] = {}

    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if not isinstance(details, dict):
                continue
            tags = tuple(details.get("tags", ["default"]))
            ep = Endpoint(method=method.upper(), path=path, tags=tags)
            endpoints.add(ep)
            for tag in tags:
                by_tag.setdefault(tag, []).append(ep)

    return ParsedSpec(
        all_endpoints=frozenset(endpoints),
        by_tag=by_tag,
    )
