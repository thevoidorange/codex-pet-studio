#!/usr/bin/env python3
"""Deterministic, dependency-free project tooling for Codex Pet Studio."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import http.server
import json
import os
import re
import shutil
import struct
import sys
import tempfile
import urllib.parse
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Sequence


CONFIG_NAME = "pet-studio.json"
PRIVATE_CONFIG_NAME = ".pet-studio-private.json"
EXPECTED_WIDTH = 1536
EXPECTED_HEIGHT = 2288
CELL_WIDTH = 192
CELL_HEIGHT = 208
EXPECTED_COLUMNS = 8
EXPECTED_ROWS = 11
MAX_SCAN_BYTES = 50 * 1024 * 1024
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)

DEFAULT_EXPORT_INCLUDE = [
    CONFIG_NAME,
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".agents/skills/pet-studio/**",
    ".github/workflows/**",
    "previewer/**",
    "templates/**",
    "examples/neutral-demo/**",
    "tests/**",
]

DESIGN_TEMPLATE_NAMES = (
    "inspiration-brief.md",
    "identity-lock.md",
    "mechanism-board.md",
    "state-choreography.md",
    "motion-bible.md",
    "qa-report.md",
    "asset-attribution.md",
)

SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


class StudioError(Exception):
    def __init__(self, message: str, *hints: str):
        super().__init__(message)
        self.hints = [hint for hint in hints if hint]


@dataclass(frozen=True)
class Finding:
    path: str
    kind: str
    detail: str
    line: int | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": self.path,
            "kind": self.kind,
            "detail": self.detail,
        }
        if self.line is not None:
            result["line"] = self.line
        return result


def emit_error(error: StudioError) -> None:
    print(f"ERROR: {error}", file=sys.stderr)
    for hint in error.hints:
        print(f"  -> {hint}", file=sys.stderr)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug:
        slug = "my-pet"
    return slug[:64]


def find_project_root(start: Path) -> Path:
    current = start.expanduser().resolve()
    for candidate in (current, *current.parents):
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    return current


def resolve_root(raw_root: str | None, *, for_init: bool = False) -> Path:
    candidate = Path(raw_root).expanduser() if raw_root else Path.cwd()
    candidate = candidate.resolve()
    if for_init:
        return candidate
    return find_project_root(candidate)


def safe_relative_path(value: str, field: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise StudioError(
            f"{field} must be a safe project-relative path; got {value!r}.",
            "Remove an absolute prefix and any '..' segments.",
        )
    return path


def project_path(root: Path, value: str, field: str) -> Path:
    relative = safe_relative_path(value, field)
    result = root.joinpath(*relative.parts).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError as exc:
        raise StudioError(f"{field} escapes the project root.") from exc
    return result


def default_config(root: Path, name: str | None, project_id: str | None) -> dict[str, Any]:
    display_name = (name or root.name.replace("-", " ").strip() or "My Pet").strip()
    pet_id = slugify(project_id or display_name)
    return {
        "$schema": ".agents/skills/pet-studio/schemas/project.schema.json",
        "schemaVersion": 1,
        "project": {
            "id": pet_id,
            "displayName": display_name,
            "defaultLocale": "en",
            "locales": ["en", "zh-CN"],
        },
        "paths": {
            "pet": "build/pet",
            "previewer": "previewer",
            "exports": "dist",
        },
        "privacy": {
            "privateTermsFile": PRIVATE_CONFIG_NAME,
        },
        "export": {
            "include": DEFAULT_EXPORT_INCLUDE,
        },
    }


def validate_config(config: Any, path: Path) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise StudioError(f"{path} must contain one JSON object.")
    if config.get("schemaVersion") != 1:
        raise StudioError(
            f"{path} has unsupported schemaVersion {config.get('schemaVersion')!r}.",
            "Set schemaVersion to 1.",
        )
    project = config.get("project")
    paths = config.get("paths")
    export = config.get("export")
    if not isinstance(project, dict):
        raise StudioError(f"{path}: project must be an object.")
    pet_id = project.get("id")
    display_name = project.get("displayName")
    if not isinstance(pet_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", pet_id):
        raise StudioError(
            f"{path}: project.id must be a lowercase, filesystem-safe id.",
            "Use letters, digits, dots, underscores, or hyphens.",
        )
    if not isinstance(display_name, str) or not display_name.strip():
        raise StudioError(f"{path}: project.displayName must be a non-empty string.")
    locales = project.get("locales")
    if not isinstance(locales, list) or not locales or not all(
        isinstance(item, str) and item for item in locales
    ):
        raise StudioError(f"{path}: project.locales must be a non-empty string array.")
    if project.get("defaultLocale") not in locales:
        raise StudioError(f"{path}: project.defaultLocale must appear in project.locales.")
    if not isinstance(paths, dict):
        raise StudioError(f"{path}: paths must be an object.")
    for key in ("pet", "previewer", "exports"):
        value = paths.get(key)
        if not isinstance(value, str):
            raise StudioError(f"{path}: paths.{key} must be a string.")
        safe_relative_path(value, f"paths.{key}")
    if not isinstance(export, dict) or not isinstance(export.get("include"), list):
        raise StudioError(f"{path}: export.include must be an array.")
    for index, pattern in enumerate(export["include"]):
        if not isinstance(pattern, str) or not pattern:
            raise StudioError(f"{path}: export.include[{index}] must be a non-empty string.")
        safe_relative_path(pattern.replace("*", "x"), f"export.include[{index}]")
    return config


def load_config(root: Path, *, required: bool = True) -> dict[str, Any] | None:
    path = root / CONFIG_NAME
    if not path.is_file():
        if required:
            raise StudioError(
                f"No {CONFIG_NAME} found at {root}.",
                f"Run `studio.py init --root {root}` first.",
            )
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StudioError(f"Cannot read {path}: {exc}") from exc
    return validate_config(value, path)


def read_private_terms(root: Path, config: dict[str, Any] | None, cli_terms: Sequence[str]) -> list[str]:
    terms: list[str] = [term.strip() for term in cli_terms if term.strip()]
    env_terms = os.environ.get("PET_STUDIO_PRIVATE_TERMS", "")
    terms.extend(item.strip() for item in env_terms.split(",") if item.strip())
    relative = PRIVATE_CONFIG_NAME
    if config:
        privacy = config.get("privacy")
        if isinstance(privacy, dict) and isinstance(privacy.get("privateTermsFile"), str):
            relative = privacy["privateTermsFile"]
    private_file = project_path(root, relative, "privacy.privateTermsFile")
    if private_file.is_file():
        try:
            value = json.loads(private_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StudioError(f"Cannot read private terms file {private_file}: {exc}") from exc
        file_terms = value.get("blockedTerms") if isinstance(value, dict) else None
        if not isinstance(file_terms, list) or not all(isinstance(item, str) for item in file_terms):
            raise StudioError(f"{private_file}: blockedTerms must be a string array.")
        terms.extend(item.strip() for item in file_terms if item.strip())
    return sorted(set(terms), key=str.casefold)


def read_png_dimensions(data: bytes) -> tuple[int, int] | None:
    signature = b"\x89PNG\r\n\x1a\n"
    if len(data) < 24 or data[:8] != signature or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def read_webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 20 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    offset = 12
    while offset + 8 <= len(data):
        chunk = data[offset : offset + 4]
        size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
        payload = data[offset + 8 : offset + 8 + size]
        if chunk == b"VP8X" and len(payload) >= 10:
            width = 1 + int.from_bytes(payload[4:7], "little")
            height = 1 + int.from_bytes(payload[7:10], "little")
            return width, height
        if chunk == b"VP8L" and len(payload) >= 5 and payload[0] == 0x2F:
            b1, b2, b3, b4 = payload[1:5]
            width = 1 + b1 + ((b2 & 0x3F) << 8)
            height = 1 + (b2 >> 6) + (b3 << 2) + ((b4 & 0x0F) << 10)
            return width, height
        if chunk == b"VP8 " and len(payload) >= 10 and payload[3:6] == b"\x9d\x01\x2a":
            width = struct.unpack("<H", payload[6:8])[0] & 0x3FFF
            height = struct.unpack("<H", payload[8:10])[0] & 0x3FFF
            return width, height
        offset += 8 + size + (size % 2)
    return None


def read_image_dimensions(path: Path) -> tuple[str, int, int]:
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_SCAN_BYTES + 1)
    except OSError as exc:
        raise StudioError(f"Cannot read spritesheet {path}: {exc}") from exc
    if len(data) > MAX_SCAN_BYTES:
        raise StudioError(f"Spritesheet {path} exceeds the {MAX_SCAN_BYTES // (1024 * 1024)} MB limit.")
    dimensions = read_png_dimensions(data)
    if dimensions:
        return "PNG", dimensions[0], dimensions[1]
    dimensions = read_webp_dimensions(data)
    if dimensions:
        return "WebP", dimensions[0], dimensions[1]
    raise StudioError(
        f"{path} is not a supported PNG or WebP image.",
        "Export the atlas as PNG or WebP without renaming another file type.",
    )


def validate_pet_dir(pet_dir: Path) -> dict[str, Any]:
    pet_dir = pet_dir.expanduser().resolve()
    manifest_path = pet_dir / "pet.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise StudioError(
            f"Missing regular file {manifest_path}.",
            "The pet folder must contain pet.json and its referenced spritesheet.",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StudioError(f"Cannot read {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise StudioError(f"{manifest_path} must contain one JSON object.")
    pet_id = manifest.get("id")
    if not isinstance(pet_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", pet_id):
        raise StudioError(
            f"{manifest_path}: id must be a lowercase, filesystem-safe string.",
            "Use letters, digits, dots, underscores, or hyphens.",
        )
    for field in ("displayName", "description"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise StudioError(f"{manifest_path}: {field} must be a non-empty string.")
    version = manifest.get("spriteVersionNumber")
    if isinstance(version, bool) or version != 2:
        raise StudioError(
            f"{manifest_path}: spriteVersionNumber must be 2; got {version!r}.",
            "Codex Pet v2 requires the full 8x11 atlas.",
        )
    spritesheet_value = manifest.get("spritesheetPath")
    if not isinstance(spritesheet_value, str):
        raise StudioError(f"{manifest_path}: spritesheetPath must be a string.")
    relative = safe_relative_path(spritesheet_value, "spritesheetPath")
    spritesheet = pet_dir.joinpath(*relative.parts).resolve()
    try:
        spritesheet.relative_to(pet_dir)
    except ValueError as exc:
        raise StudioError(f"{manifest_path}: spritesheetPath escapes the pet folder.") from exc
    if not spritesheet.is_file() or spritesheet.is_symlink():
        raise StudioError(f"Missing regular spritesheet file {spritesheet}.")
    image_format, width, height = read_image_dimensions(spritesheet)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise StudioError(
            f"{spritesheet}: expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}, got {width}x{height}.",
            f"Use {EXPECTED_COLUMNS} columns x {EXPECTED_ROWS} rows of "
            f"{CELL_WIDTH}x{CELL_HEIGHT} cells.",
        )
    if width // CELL_WIDTH != EXPECTED_COLUMNS or height // CELL_HEIGHT != EXPECTED_ROWS:
        raise StudioError(f"{spritesheet}: atlas cell geometry is invalid.")
    return {
        "ok": True,
        "petId": pet_id,
        "petDir": str(pet_dir),
        "manifest": str(manifest_path),
        "spritesheet": str(spritesheet),
        "format": image_format,
        "width": width,
        "height": height,
        "columns": EXPECTED_COLUMNS,
        "rows": EXPECTED_ROWS,
        "cellWidth": CELL_WIDTH,
        "cellHeight": CELL_HEIGHT,
    }


def relative_label(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def iter_project_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if relative.as_posix() == PRIVATE_CONFIG_NAME:
            continue
        if path.is_file() or path.is_symlink():
            yield path


def compile_path_patterns() -> list[re.Pattern[str]]:
    unix_user_root = "/" + "(?:" + "Users" + "|" + "home" + ")" + "/[^/\\s\"'<>]+/"
    windows_user_root = r"[A-Za-z]:\\(?:Users)\\[^\\\s\"'<>]+\\"
    temp_root = "/" + "(?:private/)?" + "var/folders" + r"/[^\s\"'<>]+"
    file_uri = "file:" + r"///(?:Users|home)/"
    fragments = [
        "Library" + "/Containers",
        "xwechat" + "_files",
        "RW" + "Temp",
        "codex-" + "clipboard",
    ]
    return [
        re.compile(unix_user_root),
        re.compile(windows_user_root, re.IGNORECASE),
        re.compile(temp_root),
        re.compile(file_uri, re.IGNORECASE),
        *(re.compile(re.escape(fragment), re.IGNORECASE) for fragment in fragments),
    ]


def compile_secret_patterns() -> list[tuple[str, re.Pattern[str]]]:
    return [
        ("openai_key", re.compile(re.escape("sk" + "-") + r"[A-Za-z0-9_-]{20,}")),
        ("github_token", re.compile(re.escape("ghp" + "_") + r"[A-Za-z0-9]{20,}")),
        (
            "github_pat",
            re.compile(re.escape("github" + "_pat_") + r"[A-Za-z0-9_]{20,}"),
        ),
        ("aws_access_key", re.compile(re.escape("AK" + "IA") + r"[0-9A-Z]{16}")),
        (
            "private_key",
            re.compile(
                re.escape("BEGIN" + " ")
                + r"(?:RSA|OPENSSH|EC)"
                + re.escape(" PRIVATE KEY")
            ),
        ),
        (
            "assigned_secret",
            re.compile(
                r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\b"
                r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"
            ),
        ),
    ]


PATH_PATTERNS = compile_path_patterns()
SECRET_PATTERNS = compile_secret_patterns()


def image_metadata_markers(path: Path, data: bytes) -> list[str]:
    markers: list[str] = []
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        offset = 8
        while offset + 12 <= len(data):
            size = struct.unpack(">I", data[offset : offset + 4])[0]
            kind = data[offset + 4 : offset + 8]
            if kind in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
                markers.append(kind.decode("ascii"))
            offset += 12 + size
            if kind == b"IEND":
                break
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        offset = 12
        while offset + 8 <= len(data):
            kind = data[offset : offset + 4]
            size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
            if kind in {b"EXIF", b"XMP "}:
                markers.append(kind.decode("ascii").strip())
            offset += 8 + size + (size % 2)
    elif data.startswith((b"\xff\xd8\xff",)):
        if b"Exif\x00\x00" in data:
            markers.append("EXIF")
        if b"http://ns.adobe.com/xap/1.0/" in data:
            markers.append("XMP")
        if b"Photoshop 3.0" in data:
            markers.append("IPTC")
        if b"\xff\xfe" in data:
            markers.append("COM")
    elif data.startswith((b"GIF87a", b"GIF89a")):
        if b"\x21\xfe" in data:
            markers.append("comment")
        if b"XMP DataXMP" in data:
            markers.append("XMP")
    return sorted(set(markers))


def scan_text(
    label: str,
    text: str,
    private_terms: Sequence[str],
) -> list[Finding]:
    findings: list[Finding] = []
    folded_terms = [(term, term.casefold()) for term in private_terms]
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in PATH_PATTERNS:
            if pattern.search(line):
                findings.append(
                    Finding(label, "absolute_or_private_path", "local path or app cache reference", line_number)
                )
                break
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(label, kind, "possible credential", line_number))
        folded_line = line.casefold()
        for original, folded in folded_terms:
            if folded and folded in folded_line:
                findings.append(Finding(label, "private_term", f"contains blocked term {original!r}", line_number))
    return findings


def scan_blob(
    label: str,
    data: bytes,
    suffix: str,
    private_terms: Sequence[str],
) -> list[Finding]:
    findings: list[Finding] = []
    lowered_suffix = suffix.casefold()
    if lowered_suffix in IMAGE_SUFFIXES or data.startswith(
        (b"\x89PNG\r\n\x1a\n", b"RIFF", b"\xff\xd8\xff", b"GIF87a", b"GIF89a")
    ):
        for marker in image_metadata_markers(Path(label), data):
            findings.append(Finding(label, "image_metadata", f"embedded {marker} metadata"))
        return findings
    is_probably_text = lowered_suffix in TEXT_SUFFIXES or b"\x00" not in data[:4096]
    if is_probably_text:
        text = data.decode("utf-8", errors="replace")
        findings.extend(scan_text(label, text, private_terms))
    return findings


def scan_zip(path: Path, label: str, private_terms: Sequence[str]) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with zipfile.ZipFile(path) as archive:
            total = 0
            for index, info in enumerate(archive.infolist()):
                if index >= 10000:
                    findings.append(Finding(label, "archive_limit", "archive contains more than 10,000 entries"))
                    break
                if info.is_dir():
                    continue
                entry = PurePosixPath(info.filename)
                if entry.is_absolute() or ".." in entry.parts:
                    findings.append(Finding(label, "unsafe_archive_path", info.filename))
                    continue
                total += info.file_size
                if info.file_size > MAX_SCAN_BYTES or total > MAX_SCAN_BYTES:
                    findings.append(Finding(label, "archive_limit", "archive scan exceeds 50 MB"))
                    break
                data = archive.read(info)
                entry_label = f"{label}!/{info.filename}"
                findings.extend(scan_text(entry_label, info.filename, private_terms))
                findings.extend(scan_blob(entry_label, data, entry.suffix, private_terms))
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        findings.append(Finding(label, "invalid_archive", str(exc)))
    return findings


def privacy_scan_files(root: Path, files: Iterable[Path], private_terms: Sequence[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        label = relative_label(path, root)
        findings.extend(scan_text(label, label, private_terms))
        if path.is_symlink():
            findings.append(Finding(label, "symlink", "symlinks are not allowed in shareable content"))
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            findings.append(Finding(label, "read_error", str(exc)))
            continue
        if size > MAX_SCAN_BYTES:
            findings.append(Finding(label, "oversized_file", "file exceeds the 50 MB scan limit"))
            continue
        if path.suffix.casefold() == ".zip":
            findings.extend(scan_zip(path, label, private_terms))
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            findings.append(Finding(label, "read_error", str(exc)))
            continue
        findings.extend(scan_blob(label, data, path.suffix, private_terms))
    unique: dict[tuple[str, str, str, int | None], Finding] = {}
    for finding in findings:
        unique[(finding.path, finding.kind, finding.detail, finding.line)] = finding
    return sorted(
        unique.values(),
        key=lambda item: (item.path, item.line or 0, item.kind, item.detail),
    )


def privacy_payload(root: Path, findings: Sequence[Finding], files_scanned: int) -> dict[str, Any]:
    return {
        "ok": not findings,
        "root": str(root),
        "filesScanned": files_scanned,
        "findingCount": len(findings),
        "findings": [finding.as_dict() for finding in findings],
    }


def print_privacy_result(payload: dict[str, Any]) -> None:
    if payload["ok"]:
        print(f"OK: privacy check passed ({payload['filesScanned']} files scanned).")
        return
    print(f"ERROR: privacy check found {payload['findingCount']} issue(s).", file=sys.stderr)
    for finding in payload["findings"][:100]:
        location = finding["path"]
        if "line" in finding:
            location += f":{finding['line']}"
        print(f"  - {location}: {finding['kind']} — {finding['detail']}", file=sys.stderr)
    if len(payload["findings"]) > 100:
        print("  - additional findings omitted; use --json for the complete result", file=sys.stderr)


def path_matches(rel: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.endswith("/**"):
        prefix = normalized[:-3].rstrip("/")
        return rel == prefix or rel.startswith(prefix + "/")
    return fnmatch.fnmatchcase(rel, normalized)


def collect_export_files(root: Path, patterns: Sequence[str]) -> list[Path]:
    selected: list[Path] = []
    for path in iter_project_files(root):
        rel = path.relative_to(root).as_posix()
        if any(path_matches(rel, pattern) for pattern in patterns):
            selected.append(path)
    return selected


def stable_zip_info(name: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = (mode & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def add_bytes_to_zip(archive: zipfile.ZipFile, name: str, data: bytes, executable: bool = False) -> None:
    archive.writestr(stable_zip_info(name, executable), data, compress_type=zipfile.ZIP_DEFLATED)


def ensure_local_workspace(root: Path) -> list[str]:
    created: list[str] = []
    private_path = root / PRIVATE_CONFIG_NAME
    if not private_path.exists():
        write_json(private_path, {"blockedTerms": []})
        created.append(PRIVATE_CONFIG_NAME)
    for relative in ("inputs", "design", "build/pet", "dist"):
        path = root / relative
        if not path.exists():
            path.mkdir(parents=True)
            created.append(relative + "/")
    keep_file = root / "inputs" / ".gitkeep"
    if not keep_file.exists():
        keep_file.touch()
        created.append("inputs/.gitkeep")
    template_dir = root / "templates"
    design_dir = root / "design"
    for name in DESIGN_TEMPLATE_NAMES:
        source = template_dir / name
        target = design_dir / name
        if source.is_file() and not target.exists():
            shutil.copy2(source, target)
            created.append(f"design/{name}")
    return created


def command_init(args: argparse.Namespace) -> int:
    root = resolve_root(args.root, for_init=True)
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / CONFIG_NAME
    if config_path.exists() and not args.force:
        config = load_config(root)
        created = ensure_local_workspace(root)
        print(f"OK: Pet Studio project already initialized at {root}")
        if created:
            print(f"  created local workspace files: {len(created)}")
        else:
            print("  local workspace is ready")
    else:
        config = default_config(root, args.name, args.project_id)
        write_json(config_path, config)
        ensure_local_workspace(root)
        print(f"OK: initialized Pet Studio project at {root}")
    print(f"  project id: {config['project']['id']}")
    print(f"  private terms: {PRIVATE_CONFIG_NAME} (keep this file out of git)")
    print("Next: add inspiration under inputs/, list private names in the local private-terms file,")
    print("then run `studio.py doctor`.")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "name": "python",
            "ok": sys.version_info >= (3, 9),
            "detail": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
    )
    try:
        config = load_config(root)
        checks.append({"name": "config", "ok": True, "detail": CONFIG_NAME})
    except StudioError as exc:
        checks.append({"name": "config", "ok": False, "detail": str(exc)})
        config = None
    if config:
        private_relative = config.get("privacy", {}).get("privateTermsFile", PRIVATE_CONFIG_NAME)
        private_path = project_path(root, private_relative, "privacy.privateTermsFile")
        try:
            read_private_terms(root, config, [])
            checks.append(
                {
                    "name": "private-settings",
                    "ok": True,
                    "detail": private_path.name if private_path.exists() else "not created yet",
                }
            )
        except StudioError as exc:
            checks.append({"name": "private-settings", "ok": False, "detail": str(exc)})
        preview_dir = project_path(root, config["paths"]["previewer"], "paths.previewer")
        preview_index = preview_dir / "index.html"
        checks.append(
            {
                "name": "previewer",
                "ok": preview_index.is_file(),
                "warning": not preview_index.is_file(),
                "detail": relative_label(preview_index, root),
            }
        )
        pet_dir = project_path(root, config["paths"]["pet"], "paths.pet")
        if (pet_dir / "pet.json").exists():
            try:
                result = validate_pet_dir(pet_dir)
                checks.append(
                    {
                        "name": "pet-v2",
                        "ok": True,
                        "detail": f"{result['format']} {result['width']}x{result['height']}",
                    }
                )
            except StudioError as exc:
                checks.append({"name": "pet-v2", "ok": False, "detail": str(exc)})
        else:
            checks.append(
                {
                    "name": "pet-v2",
                    "ok": True,
                    "warning": True,
                    "detail": "not built yet",
                }
            )
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    hatch_candidates = (
        codex_home / "skills" / "hatch-pet" / "SKILL.md",
        root / ".agents" / "skills" / "hatch-pet" / "SKILL.md",
    )
    hatch_path = next((path for path in hatch_candidates if path.is_file()), None)
    checks.append(
        {
            "name": "hatch-pet",
            "ok": True,
            "warning": hatch_path is None,
            "detail": (
                str(hatch_path)
                if hatch_path
                else "not found in standard local skill paths; needed only for production"
            ),
        }
    )
    ok = all(item["ok"] for item in checks)
    payload = {"ok": ok, "root": str(root), "checks": checks}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in checks:
            status = "WARN" if item.get("warning") else ("OK" if item["ok"] else "FAIL")
            print(f"{status}: {item['name']} — {item['detail']}")
    return 0 if ok else 1


def command_validate(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    config = load_config(root)
    pet_dir = (
        Path(args.pet_dir).expanduser().resolve()
        if args.pet_dir
        else project_path(root, config["paths"]["pet"], "paths.pet")
    )
    result = validate_pet_dir(pet_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"OK: valid Codex Pet v2 `{result['petId']}` — "
            f"{result['format']} {result['width']}x{result['height']}, "
            f"{result['columns']}x{result['rows']} cells."
        )
    return 0


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"preview: {format_string % args}")


def command_preview(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    config = load_config(root)
    preview_relative = config["paths"]["previewer"]
    preview_dir = project_path(root, preview_relative, "paths.previewer")
    if not (preview_dir / "index.html").is_file():
        raise StudioError(
            f"Previewer entry not found at {preview_dir / 'index.html'}.",
            "Restore the repository previewer or update paths.previewer.",
        )
    loopback_hosts = {"127.0.0.1", "localhost", "::1"}
    if args.host not in loopback_hosts and not args.allow_network:
        raise StudioError(
            f"Refusing to expose the previewer on non-loopback host {args.host!r}.",
            "Use --allow-network only on a trusted network.",
        )
    quoted_path = "/".join(urllib.parse.quote(part) for part in PurePosixPath(preview_relative).parts)
    shown_host = "127.0.0.1" if args.host in {"::1", "localhost"} else args.host
    planned_url = f"http://{shown_host}:{args.port}/{quoted_path}/"
    if args.check:
        print(f"OK: previewer is ready at {planned_url}")
        return 0

    def handler(*handler_args: Any, **handler_kwargs: Any) -> NoCacheHandler:
        return NoCacheHandler(*handler_args, directory=str(root), **handler_kwargs)

    try:
        server = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        raise StudioError(
            f"Cannot start preview server on {args.host}:{args.port}: {exc}",
            "Choose another port with --port.",
        ) from exc
    actual_port = server.server_address[1]
    url = f"http://{shown_host}:{actual_port}/{quoted_path}/"
    print(f"OK: previewer running at {url}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped previewer.")
    finally:
        server.server_close()
    return 0


def command_privacy_check(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    config = load_config(root, required=False)
    terms = read_private_terms(root, config, args.blocked_term)
    files = list(iter_project_files(root))
    findings = privacy_scan_files(root, files, terms)
    payload = privacy_payload(root, findings, len(files))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_privacy_result(payload)
    return 0 if payload["ok"] else 1


def command_export(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    config = load_config(root)
    patterns = list(config["export"]["include"])
    files = collect_export_files(root, patterns)
    pet_result: dict[str, Any] | None = None
    if args.include_pet:
        pet_dir = project_path(root, config["paths"]["pet"], "paths.pet")
        pet_result = validate_pet_dir(pet_dir)
        manifest_path = Path(pet_result["manifest"])
        spritesheet_path = Path(pet_result["spritesheet"])
        for pet_file in (manifest_path, spritesheet_path):
            if pet_file not in files:
                files.append(pet_file)
    files = sorted(set(files), key=lambda path: relative_label(path, root))
    if not files:
        raise StudioError(
            "The export allowlist selected no files.",
            "Check export.include in pet-studio.json.",
        )
    private_terms = read_private_terms(root, config, args.blocked_term)
    findings = privacy_scan_files(root, files, private_terms)
    if findings:
        payload = privacy_payload(root, findings, len(files))
        print_privacy_result(payload)
        raise StudioError("Export stopped because selected files failed privacy-check.")
    exports_dir = project_path(root, config["paths"]["exports"], "paths.exports")
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else exports_dir / f"{config['project']['id']}-studio.zip"
    )
    if output.exists() and not args.force:
        raise StudioError(
            f"Export already exists at {output}.",
            "Choose another --output or pass --force.",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    file_entries: list[dict[str, Any]] = []
    for path in files:
        data = path.read_bytes()
        file_entries.append(
            {
                "path": relative_label(path, root),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {
        "schemaVersion": 1,
        "kind": "pet-studio-export",
        "projectId": config["project"]["id"],
        "includesPet": bool(pet_result),
        "files": file_entries,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    temporary = output.parent / f".{output.name}.tmp-{os.getpid()}"
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                rel = relative_label(path, root)
                executable = bool(path.stat().st_mode & 0o111)
                add_bytes_to_zip(archive, rel, path.read_bytes(), executable)
            add_bytes_to_zip(archive, "export-manifest.json", manifest_bytes)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"OK: exported {len(files)} allowlisted files to {output}")
    print(f"  sha256: {digest}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    config = load_config(root)
    pet_dir = (
        Path(args.pet_dir).expanduser().resolve()
        if args.pet_dir
        else project_path(root, config["paths"]["pet"], "paths.pet")
    )
    result = validate_pet_dir(pet_dir)
    destination = Path(args.destination).expanduser().resolve()
    if destination == Path(destination.anchor) or destination == Path.home().resolve():
        raise StudioError(
            f"Refusing broad install destination {destination}.",
            "Pass an explicit pets directory, not the filesystem root or home directory.",
        )
    target = destination / result["petId"]
    if target.exists() and not args.replace:
        raise StudioError(
            f"Pet already exists at {target}.",
            "Use --replace to preserve the existing pet as a timestamped backup.",
        )
    if args.check:
        print(f"OK: install plan validated; `{result['petId']}` would be installed at {target}")
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    temporary = destination / f".{result['petId']}.installing-{os.getpid()}"
    if temporary.exists():
        raise StudioError(f"Temporary install path already exists: {temporary}")
    backup: Path | None = None
    try:
        temporary.mkdir()
        manifest_source = Path(result["manifest"])
        spritesheet_source = Path(result["spritesheet"])
        relative_sheet = spritesheet_source.relative_to(pet_dir)
        shutil.copy2(manifest_source, temporary / "pet.json")
        copied_sheet = temporary / relative_sheet
        copied_sheet.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spritesheet_source, copied_sheet)
        validate_pet_dir(temporary)
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = destination / f".{result['petId']}.backup-{stamp}"
            if backup.exists():
                raise StudioError(f"Backup path already exists: {backup}")
            target.rename(backup)
        temporary.rename(target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        if backup is not None and backup.exists() and not target.exists():
            backup.rename(target)
        raise
    print(f"OK: installed `{result['petId']}` at {target}")
    if backup:
        print(f"  previous version preserved at {backup}")
    return 0


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", help="project root (default: current directory or nearest parent)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="studio.py",
        description="Dependency-free project, validation, privacy, preview, export, and install tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize a safe Pet Studio project")
    add_root_argument(init_parser)
    init_parser.add_argument("--name", help="human-readable project name")
    init_parser.add_argument("--id", dest="project_id", help="lowercase project id")
    init_parser.add_argument("--force", action="store_true", help="replace the public project config")
    init_parser.set_defaults(func=command_init)

    doctor_parser = subparsers.add_parser("doctor", help="check project readiness")
    add_root_argument(doctor_parser)
    doctor_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    doctor_parser.set_defaults(func=command_doctor)

    preview_parser = subparsers.add_parser("preview", help="serve the local previewer")
    add_root_argument(preview_parser)
    preview_parser.add_argument("--host", default="127.0.0.1")
    preview_parser.add_argument("--port", type=int, default=8765)
    preview_parser.add_argument(
        "--allow-network",
        action="store_true",
        help="allow a non-loopback host on a trusted network",
    )
    preview_parser.add_argument("--check", action="store_true", help="validate and print the URL without serving")
    preview_parser.set_defaults(func=command_preview)

    validate_parser = subparsers.add_parser("validate", help="validate a Codex Pet v2 package")
    add_root_argument(validate_parser)
    validate_parser.add_argument("--pet-dir", help="pet package directory (default: config paths.pet)")
    validate_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    validate_parser.set_defaults(func=command_validate)

    privacy_parser = subparsers.add_parser(
        "privacy-check",
        help="scan for local paths, private terms, credentials, and image metadata",
    )
    add_root_argument(privacy_parser)
    privacy_parser.add_argument(
        "--blocked-term",
        action="append",
        default=[],
        help="additional private term to block (repeatable)",
    )
    privacy_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    privacy_parser.set_defaults(func=command_privacy_check)

    export_parser = subparsers.add_parser("export", help="create a deterministic allowlisted share bundle")
    add_root_argument(export_parser)
    export_parser.add_argument("--output", help="zip output path")
    export_parser.add_argument(
        "--include-pet",
        action="store_true",
        help="include the validated build/pet package",
    )
    export_parser.add_argument(
        "--blocked-term",
        action="append",
        default=[],
        help="additional private term to block (repeatable)",
    )
    export_parser.add_argument("--force", action="store_true", help="replace an existing output")
    export_parser.set_defaults(func=command_export)

    install_parser = subparsers.add_parser(
        "install",
        help="install a validated pet to an explicit destination",
    )
    add_root_argument(install_parser)
    install_parser.add_argument("--pet-dir", help="pet package directory (default: config paths.pet)")
    install_parser.add_argument(
        "--destination",
        required=True,
        help="explicit pets root; the pet id is added beneath it",
    )
    install_parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing pet while preserving a timestamped backup",
    )
    install_parser.add_argument("--check", action="store_true", help="validate the install plan only")
    install_parser.set_defaults(func=command_install)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except StudioError as exc:
        emit_error(exc)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except OSError as exc:
        emit_error(StudioError(f"Filesystem operation failed: {exc}"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
