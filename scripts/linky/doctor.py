from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from typing import Any, Callable

from .strategy import load_strategy


ModuleChecker = Callable[[str], bool]
CommandChecker = Callable[[str], bool]

DEFAULT_MODULES = ["markitdown", "trafilatura", "scrapling", "html2text"]
COMMAND_REQUIREMENTS = {"playwright-cli"}


def doctor_report(
    strategy_path: str | Path | None = None,
    *,
    strategy: dict[str, Any] | None = None,
    module_checker: ModuleChecker | None = None,
    command_checker: CommandChecker | None = None,
) -> dict[str, Any]:
    if strategy is None:
        if strategy_path is None:
            strategy_path = Path(__file__).resolve().parents[2] / "references" / "fetch-strategy.toml"
        strategy = load_strategy(strategy_path)

    module_checker = module_checker or _module_available
    command_checker = command_checker or _command_available

    modules = {name: _status(module_checker(name)) for name in DEFAULT_MODULES}
    commands = {"playwright-cli": _status(command_checker("playwright-cli"))}
    providers = []

    for provider in strategy.get("fallback_chain", []):
        provider_id = provider.get("id", "unknown")
        if provider.get("enabled", True) is False:
            providers.append({"id": provider_id, "status": "disabled", "missing": [], "requirements": provider.get("requires", [])})
            continue

        requirements = list(provider.get("requires", []))
        missing = []
        for requirement in requirements:
            if _is_command_requirement(requirement):
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


def _status(ok: bool) -> str:
    return "ready" if ok else "missing"


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command_available(name: str) -> bool:
    return shutil.which(name) is not None
