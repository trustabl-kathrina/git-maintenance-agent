"""Path and output protections shared by every repository tool."""

from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path

from .errors import UnsafePathError

DENIED_DIRECTORY_NAMES = {".git", ".hg", ".svn", ".ssh", ".aws", ".gnupg", "node_modules"}
DENIED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "credentials.json",
}
DENIED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".der", ".crt"}
DENIED_PATTERNS = ("*.env", "*.env.*", "*secret*", "*credential*")
DEFAULT_OUTPUT_LIMIT = 48_000


def truncate_output(value: str, limit: int = DEFAULT_OUTPUT_LIMIT) -> str:
    """Bound model-facing tool output while preserving the truncation signal."""

    if len(value) <= limit:
        return value
    return f"{value[:limit]}\n[output truncated at {limit} characters]"


def sha256_file(path: Path) -> str:
    """Return a content hash used to invalidate stale patch proposals."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sensitive_relative_path(relative_path: Path) -> bool:
    """Identify credential-like paths before they reach a model or report."""

    lowered_parts = [part.lower() for part in relative_path.parts]
    if any(part in DENIED_DIRECTORY_NAMES for part in lowered_parts[:-1]):
        return True
    filename = relative_path.name.lower()
    if filename in DENIED_FILE_NAMES or relative_path.suffix.lower() in DENIED_SUFFIXES:
        return True
    return any(fnmatch.fnmatch(filename, pattern) for pattern in DENIED_PATTERNS)


def resolve_safe_path(
    workspace_root: Path, candidate: str | Path, *, must_exist: bool = True
) -> Path:
    """Resolve a non-sensitive path and ensure it stays inside the workspace."""

    root = workspace_root.resolve()
    path = (
        (root / candidate).resolve()
        if not Path(candidate).is_absolute()
        else Path(candidate).resolve()
    )
    try:
        relative_path = path.relative_to(root)
    except ValueError as error:
        raise UnsafePathError(f"Path escapes the repository: {candidate}") from error
    if is_sensitive_relative_path(relative_path):
        raise UnsafePathError(f"Sensitive path is unavailable to the agent: {relative_path}")
    if must_exist and not path.exists():
        raise UnsafePathError(f"Path does not exist: {relative_path}")
    return path
