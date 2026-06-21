from __future__ import annotations

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


def load_strategy(path: str | Path) -> dict[str, Any]:
    strategy_path = Path(path).expanduser()
    with strategy_path.open("rb") as f:
        return tomllib.load(f)


def fallback_ids(strategy: dict[str, Any]) -> list[str]:
    return [item["id"] for item in strategy.get("fallback_chain", []) if "id" in item]


def provider_config(strategy: dict[str, Any], provider_id: str) -> dict[str, Any]:
    for item in strategy.get("fallback_chain", []):
        if item.get("id") == provider_id:
            return dict(item)
    providers = strategy.get("providers", {})
    if isinstance(providers, dict) and isinstance(providers.get(provider_id), dict):
        return dict(providers[provider_id])
    return {}


def quality_threshold(strategy: dict[str, Any]) -> float:
    quality = strategy.get("quality", {})
    return float(quality.get("min_score", strategy.get("global", {}).get("quality_threshold", 0.55)))


def trace_enabled(strategy: dict[str, Any]) -> bool:
    return bool(strategy.get("trace", {}).get("enabled", True))


def graph_enabled(strategy: dict[str, Any]) -> bool:
    return bool(strategy.get("graph", {}).get("enabled", True))


def domain_for_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def _domain_matches(domain: str, pattern: str) -> bool:
    pattern = pattern.lower().removeprefix("www.")
    return domain == pattern or domain.endswith("." + pattern)


def matching_domain_route(url: str, strategy: dict[str, Any]) -> dict[str, Any] | None:
    domain = domain_for_url(url)
    for route in strategy.get("domain_routes", []):
        pattern = route.get("pattern")
        if pattern and _domain_matches(domain, pattern):
            return dict(route)
    return None


def resolve_provider_chain(url: str, strategy: dict[str, Any]) -> list[str]:
    chain = fallback_ids(strategy)
    route = matching_domain_route(url, strategy)
    if not route:
        return chain

    skip = set(route.get("skip_layers", []))
    go_to = route.get("go_to")
    filtered = [provider for provider in chain if provider not in skip]

    if go_to and go_to in filtered:
        start = filtered.index(go_to)
        return filtered[start:]
    if go_to:
        return [go_to] + [provider for provider in filtered if provider != go_to]
    return filtered
