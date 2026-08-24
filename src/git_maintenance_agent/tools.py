"""Typed tool facade exposed to the orchestrator and live agent runtime."""

from __future__ import annotations

from dataclasses import dataclass

from .models import CommandResult
from .workspace import Workspace


@dataclass(slots=True)
class RepositoryTools:
    """Narrow repository operations. No arbitrary shell or network capability exists."""

    workspace: Workspace
    allow_test_execution: bool

    def read_file(self, path: str) -> str:
        return self.workspace.read_file(path)

    def list_files(self, directory: str = ".") -> list[str]:
        return self.workspace.list_files(directory)

    def search_code(self, query: str) -> list[dict[str, object]]:
        return self.workspace.search_code(query)

    def git_status(self) -> CommandResult:
        return self.workspace.git("status", "--short")

    def git_diff(self) -> CommandResult:
        return self.workspace.git("diff", "--no-ext-diff")

    def git_log(self, limit: int = 10) -> CommandResult:
        safe_limit = max(1, min(limit, 50))
        return self.workspace.git("log", f"--max-count={safe_limit}", "--oneline", "--decorate")

    def git_show(self, revision: str = "HEAD") -> CommandResult:
        if revision.startswith("-") or any(character.isspace() for character in revision):
            raise ValueError("Git revision must be a single revision token.")
        return self.workspace.git("show", "--stat", "--oneline", revision)

    def run_pytest(self, nodeid: str | None = None) -> CommandResult:
        return self.workspace.run_pytest(nodeid, approved=self.allow_test_execution)
