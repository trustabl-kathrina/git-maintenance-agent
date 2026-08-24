"""Constrained access to a local Git repository."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .errors import ConsentRequiredError, GitMaintenanceAgentError, UnsafePathError
from .models import CommandResult
from .safety import is_sensitive_relative_path, resolve_safe_path, truncate_output


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: int = 120,
    input_text: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> CommandResult:
    """Run an allowlisted command without shell interpolation."""

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
            env=environment,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout or ""
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr or ""
        return CommandResult(
            command=command,
            exit_code=None,
            stdout=truncate_output(stdout),
            stderr=truncate_output(stderr),
            timed_out=True,
        )
    return CommandResult(
        command=command,
        exit_code=completed.returncode,
        stdout=truncate_output(completed.stdout),
        stderr=truncate_output(completed.stderr),
    )


@dataclass(slots=True)
class Workspace:
    """A Git worktree whose tools cannot escape the repository root."""

    root: Path

    @classmethod
    def open(cls, candidate: Path) -> Workspace:
        """Locate the containing Git worktree for a user-provided directory."""

        if not candidate.exists() or not candidate.is_dir():
            raise GitMaintenanceAgentError(f"Repository directory does not exist: {candidate}")
        result = _run_command(
            ["git", "rev-parse", "--show-toplevel"], cwd=candidate, timeout_seconds=15
        )
        if result.exit_code != 0:
            raise GitMaintenanceAgentError("The target must be inside a Git worktree.")
        return cls(Path(result.stdout.strip()).resolve())

    def relative_path(self, path: Path) -> str:
        """Return a portable path for reports."""

        return path.resolve().relative_to(self.root).as_posix()

    def read_file(self, path: str) -> str:
        """Read a bounded UTF-8 repository file after policy checks."""

        safe_path = resolve_safe_path(self.root, path)
        if not safe_path.is_file():
            raise UnsafePathError(f"Not a file: {path}")
        try:
            return truncate_output(safe_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as error:
            raise UnsafePathError(f"Binary or non-UTF-8 file is unavailable: {path}") from error

    def list_files(self, relative_directory: str = ".", limit: int = 500) -> list[str]:
        """List safe files without traversing ignored sensitive directories."""

        directory = resolve_safe_path(self.root, relative_directory)
        if not directory.is_dir():
            raise UnsafePathError(f"Not a directory: {relative_directory}")
        results: list[str] = []
        for current_root, directories, filenames in os.walk(directory):
            current = Path(current_root)
            directories[:] = [
                name
                for name in directories
                if not is_sensitive_relative_path((current / name).relative_to(self.root))
            ]
            for filename in filenames:
                candidate = current / filename
                relative = candidate.relative_to(self.root)
                if is_sensitive_relative_path(relative) or not candidate.is_file():
                    continue
                results.append(relative.as_posix())
                if len(results) >= limit:
                    return results
        return results

    def search_code(self, query: str, limit: int = 50) -> list[dict[str, object]]:
        """Perform a simple, deterministic text search over safe UTF-8 files."""

        if not query.strip():
            raise GitMaintenanceAgentError("Search query cannot be empty.")
        matches: list[dict[str, object]] = []
        for relative in self.list_files(limit=2_000):
            path = self.root / relative
            if path.stat().st_size > 1_000_000:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if query.casefold() in line.casefold():
                    matches.append(
                        {"path": relative, "line": line_number, "text": truncate_output(line, 500)}
                    )
                    if len(matches) >= limit:
                        return matches
        return matches

    def git(
        self, *arguments: str, timeout_seconds: int = 30, input_text: str | None = None
    ) -> CommandResult:
        """Run a read-only Git command selected by a higher-level tool."""

        return _run_command(
            ["git", *arguments],
            cwd=self.root,
            timeout_seconds=timeout_seconds,
            input_text=input_text,
        )

    def run_pytest(
        self, nodeid: str | None, *, approved: bool, timeout_seconds: int = 120
    ) -> CommandResult:
        """Run pytest only when execution was explicitly authorized by the caller."""

        if not approved:
            raise ConsentRequiredError(
                "Pass --allow-test-execution before the agent may run pytest."
            )
        if nodeid and (nodeid.startswith("-") or any(character.isspace() for character in nodeid)):
            raise GitMaintenanceAgentError(
                "Pytest target must be a single node id and cannot be an option."
            )
        command = [sys.executable, "-m", "pytest", "-q"]
        if nodeid:
            command.append(nodeid)
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        with tempfile.TemporaryDirectory(prefix="gma-pycache-") as pycache_directory:
            # A new cache prevents stale same-second bytecode after an approved patch.
            environment["PYTHONPYCACHEPREFIX"] = pycache_directory
            return _run_command(
                command,
                cwd=self.root,
                timeout_seconds=timeout_seconds,
                environment=environment,
            )
