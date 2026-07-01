from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from typing import Any, Callable

from .strategy import load_strategy


ModuleChecker = Callable[[str], bool]
CommandChecker = Callable[[str], bool]
ConfigChecker = Callable[[str], bool]

DEFAULT_MODULES = ["markitdown", "trafilatura", "scrapling", "html2text", "feedparser"]
COMMAND_REQUIREMENTS = {
    "playwright-cli",
    "yt-dlp",
    "gh",
    "bili",
    "twitter",
    "rdt",
    "opencli",
    "mcporter",
    "ffmpeg",
    "node",
    "deno",
    "xhs",
}
CONFIG_REQUIREMENTS = {
    "exa-mcp-config",
    "xiaohongshu-mcp-service",
    "linkedin-mcp-config",
    "xueqiu-session",
    "transcription-provider",
}


def doctor_report(
    strategy_path: str | Path | None = None,
    *,
    strategy: dict[str, Any] | None = None,
    module_checker: ModuleChecker | None = None,
    command_checker: CommandChecker | None = None,
    config_checker: ConfigChecker | None = None,
) -> dict[str, Any]:
    if strategy is None:
        if strategy_path is None:
            strategy_path = Path(__file__).resolve().parents[2] / "references" / "fetch-strategy.toml"
        strategy = load_strategy(strategy_path)

    module_checker = module_checker or _module_available
    command_checker = command_checker or _command_available
    config_checker = config_checker or _config_available

    modules = {name: _status(module_checker(name)) for name in DEFAULT_MODULES}
    commands = {name: _status(command_checker(name)) for name in sorted(COMMAND_REQUIREMENTS)}
    providers = []

    provider_items = list(strategy.get("fallback_chain", []))
    dedicated = strategy.get("providers", {})
    if isinstance(dedicated, dict):
        for provider_id, provider in dedicated.items():
            if isinstance(provider, dict):
                provider_items.append({"id": provider_id, **provider})

    for provider in provider_items:
        provider_id = provider.get("id", "unknown")
        if provider.get("enabled", True) is False:
            providers.append({"id": provider_id, "status": "disabled", "missing": [], "requirements": provider.get("requires", [])})
            continue

        requirements = list(provider.get("requires", []))
        missing = []
        for requirement in requirements:
            if requirement == "node-or-deno":
                if not (command_checker("node") or command_checker("deno")):
                    missing.append(requirement)
            elif _is_config_requirement(requirement):
                if not config_checker(requirement):
                    missing.append(requirement)
            elif _is_command_requirement(requirement):
                if not command_checker(requirement):
                    missing.append(requirement)
            elif not module_checker(requirement):
                missing.append(requirement)

        providers.append(
            {
                "id": provider_id,
                "status": "missing" if missing else "ready",
                "missing": missing,
                "requirements": requirements,
            }
        )

    overall = "ready" if all(item["status"] != "missing" for item in providers) else "missing"
    return {"status": overall, "providers": providers, "modules": modules, "commands": commands}


def _is_command_requirement(requirement: str) -> bool:
    return requirement in COMMAND_REQUIREMENTS or requirement.endswith("-cli")


def _is_config_requirement(requirement: str) -> bool:
    return requirement in CONFIG_REQUIREMENTS or requirement.endswith("-config") or requirement.endswith("-service")


def _status(ok: bool) -> str:
    return "ready" if ok else "missing"


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command_available(name: str) -> bool:
    return shutil.which(name) is not None


def _config_available(name: str) -> bool:
    return False
