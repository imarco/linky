from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from .contracts import utc_now_iso


TEXT_SUFFIXES = {".md": "markdown", ".txt": "text"}
CONVERTIBLE_SUFFIXES = {".pdf": "pdf", ".docx": "office", ".pptx": "office", ".xlsx": "office"}


class SourceKind(str, Enum):
    URL = "url"
    MARKDOWN = "markdown"
    TEXT = "text"
    PDF = "pdf"
    OFFICE = "office"
    UNSUPPORTED = "unsupported"


@dataclass
class SourceInput:
    raw: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntakeTrace:
    input: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    final_status: str = "failed"
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None

    def add_step(self, name: str, status: str, **metadata: Any) -> None:
        step = {"name": name, "status": status}
        step.update({key: value for key, value in metadata.items() if value is not None})
        self.steps.append(step)

    def finish(self, status: str) -> None:
        self.final_status = status
        self.finished_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceArtifact:
    id: str
    kind: SourceKind | str
    original_uri: str
    artifact_path_or_text: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    trace: IntakeTrace | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value if isinstance(self.kind, SourceKind) else self.kind
        data["trace"] = self.trace.to_dict() if self.trace else None
        return data


ConverterFn = Callable[[Path], str]
DependencyChecker = Callable[[str], bool]


def detect_source_kind(raw: str) -> SourceKind:
    if _is_url(raw):
        return SourceKind.URL

    suffix = Path(raw).expanduser().suffix.lower()
    if suffix == ".md":
        return SourceKind.MARKDOWN
    if suffix == ".txt":
        return SourceKind.TEXT
    if suffix == ".pdf":
        return SourceKind.PDF
    if suffix in {".docx", ".pptx", ".xlsx"}:
        return SourceKind.OFFICE
    return SourceKind.UNSUPPORTED


def intake_source(
    source: str | SourceInput,
    *,
    converter: ConverterFn | None = None,
    dependency_checker: DependencyChecker | None = None,
) -> SourceArtifact:
    source_input = source if isinstance(source, SourceInput) else SourceInput(raw=str(source))
    raw = source_input.raw
    kind = detect_source_kind(raw)
    trace = IntakeTrace(input=raw)
    artifact_id = _stable_id(raw)

    if kind == SourceKind.URL:
        trace.add_step("detect", "success", kind=kind.value)
        trace.add_step("handoff", "success", pipeline="existing_url_pipeline")
        trace.finish("success")
        return SourceArtifact(
            id=artifact_id,
            kind=kind,
            original_uri=raw,
            artifact_path_or_text=raw,
            status="success",
            metadata={**source_input.metadata, "extraction_pipeline": "existing_url_pipeline"},
            quality={"status": "not_scored", "content_length": 0},
            trace=trace,
        )

    path = Path(raw).expanduser()
    trace.add_step("detect", "success", kind=kind.value, suffix=path.suffix.lower())

    if not path.exists():
        message = f"source path does not exist: {path}"
        trace.add_step("read", "failed", error=message)
        trace.finish("failed")
        return _artifact(
            artifact_id, kind, raw, "", "failed", trace, [message], source_input.metadata,
        )

    if kind in {SourceKind.MARKDOWN, SourceKind.TEXT}:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            message = str(exc)
            trace.add_step("read", "failed", error=message)
            trace.finish("failed")
            return _artifact(artifact_id, kind, raw, "", "failed", trace, [message], source_input.metadata)

        trace.add_step("read", "success", bytes=path.stat().st_size)
        trace.finish("success")
        return _artifact(
            artifact_id,
            kind,
            raw,
            text,
            "success",
            trace,
            [],
            {**source_input.metadata, **_file_metadata(path)},
            _quality_for_text(text),
        )

    if kind in {SourceKind.PDF, SourceKind.OFFICE}:
        return _convert_file(path, raw, kind, artifact_id, trace, source_input.metadata, converter, dependency_checker)

    message = f"unsupported source type: {path.suffix.lower() or 'unknown'}"
    trace.add_step("classify", "unsupported", error=message)
    trace.finish("unsupported")
    return _artifact(artifact_id, kind, raw, "", "unsupported", trace, [message], source_input.metadata)


def intake_sources(
    sources: list[str | SourceInput],
    *,
    converter: ConverterFn | None = None,
    dependency_checker: DependencyChecker | None = None,
) -> list[SourceArtifact]:
    return [
        intake_source(source, converter=converter, dependency_checker=dependency_checker)
        for source in sources
    ]


def _convert_file(
    path: Path,
    raw: str,
    kind: SourceKind,
    artifact_id: str,
    trace: IntakeTrace,
    metadata: dict[str, Any],
    converter: ConverterFn | None,
    dependency_checker: DependencyChecker | None,
) -> SourceArtifact:
    checker = dependency_checker or _has_dependency
    if converter is None and not checker("markitdown"):
        message = "markitdown is required to convert PDF/Office sources"
        trace.add_step("convert", "missing_dependency", dependency="markitdown", error=message)
        trace.finish("missing_dependency")
        return _artifact(artifact_id, kind, raw, "", "missing_dependency", trace, [message], {**metadata, **_file_metadata(path)})

    try:
        text = converter(path) if converter else _run_markitdown(path)
    except Exception as exc:
        message = str(exc)
        trace.add_step("convert", "failed", error=message)
        trace.finish("failed")
        return _artifact(artifact_id, kind, raw, "", "failed", trace, [message], {**metadata, **_file_metadata(path)})

    trace.add_step("convert", "success", dependency="markitdown", bytes=path.stat().st_size)
    trace.finish("success")
    return _artifact(
        artifact_id, kind, raw, text, "success", trace, [], {**metadata, **_file_metadata(path), "converter": "markitdown"}, _quality_for_text(text)
    )


def _artifact(
    artifact_id: str,
    kind: SourceKind,
    original_uri: str,
    artifact_path_or_text: str,
    status: str,
    trace: IntakeTrace,
    errors: list[str],
    metadata: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
) -> SourceArtifact:
    return SourceArtifact(
        id=artifact_id,
        kind=kind,
        original_uri=original_uri,
        artifact_path_or_text=artifact_path_or_text,
        status=status,
        metadata=metadata or {},
        quality=quality or {"status": status, "content_length": len(artifact_path_or_text)},
        trace=trace,
        errors=errors,
    )


def _is_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _stable_id(raw: str) -> str:
    digest = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"source:{digest}"


def _file_metadata(path: Path) -> dict[str, Any]:
    return {"path": str(path), "suffix": path.suffix.lower(), "size_bytes": path.stat().st_size}


def _quality_for_text(text: str) -> dict[str, Any]:
    length = len(text)
    return {"status": "success" if length else "partial", "content_length": length}


def _has_dependency(name: str) -> bool:
    import importlib.util
    import shutil

    return importlib.util.find_spec(name) is not None or shutil.which(name) is not None


def _run_markitdown(path: Path) -> str:
    proc = subprocess.run(["markitdown", str(path)], check=False, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"markitdown exited {proc.returncode}")
    if not proc.stdout.strip():
        raise RuntimeError("markitdown returned empty output")
    return proc.stdout
