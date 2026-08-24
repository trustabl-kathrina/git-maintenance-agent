from __future__ import annotations

import pytest

from git_maintenance_agent.errors import UnsafePathError
from git_maintenance_agent.safety import (
    is_sensitive_relative_path,
    resolve_safe_path,
    truncate_output,
)


def test_sensitive_paths_are_denied(git_repository) -> None:
    secret = git_repository.root / ".env"
    secret.write_text("OPENAI_API_KEY=not-a-real-key", encoding="utf-8")

    assert is_sensitive_relative_path(secret.relative_to(git_repository.root))
    with pytest.raises(UnsafePathError, match="Sensitive path"):
        resolve_safe_path(git_repository.root, ".env")


def test_path_escape_is_denied(git_repository, tmp_path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(UnsafePathError, match="escapes"):
        resolve_safe_path(git_repository.root, outside)


def test_output_truncation_keeps_a_signal() -> None:
    result = truncate_output("a" * 20, limit=10)

    assert result.startswith("a" * 10)
    assert "truncated" in result
