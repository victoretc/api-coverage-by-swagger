from prance.util.resolver import RefResolver

from models import Endpoint, ParsedSpec


def parse_spec(spec: dict) -> ParsedSpec:
    resolver = RefResolver(specs=spec, url="file:///spec.yaml")
    resolver.resolve_references()
    resolved = resolver.specs

    endpoints: set[Endpoint] = set()
    by_tag: dict[str, list[Endpoint]] = {}

    for path, methods in resolved.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
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
