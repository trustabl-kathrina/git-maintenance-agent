from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from git_maintenance_agent.workspace import Workspace


@pytest.fixture
def git_repository(tmp_path: Path) -> Workspace:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    return Workspace.open(tmp_path)
