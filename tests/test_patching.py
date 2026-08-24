from __future__ import annotations

import pytest

from git_maintenance_agent.errors import PatchRejectedError
from git_maintenance_agent.models import PatchProposal
from git_maintenance_agent.patching import PatchApplier

PATCH = """diff --git a/module.py b/module.py
index 0000000..1111111 100644
--- a/module.py
+++ b/module.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""


def test_prepared_patch_applies_only_to_current_text_file(git_repository) -> None:
    target = git_repository.root / "module.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    applier = PatchApplier()

    proposal = applier.prepare(
        git_repository, PatchProposal(unified_diff=PATCH, rationale="Fix value.")
    )
    result = applier.apply(git_repository, proposal)

    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"


def test_patch_rejects_a_stale_target(git_repository) -> None:
    target = git_repository.root / "module.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    applier = PatchApplier()
    proposal = applier.prepare(
        git_repository, PatchProposal(unified_diff=PATCH, rationale="Fix value.")
    )
    target.write_text("VALUE = 3\n", encoding="utf-8")

    with pytest.raises(PatchRejectedError, match="Target changed"):
        applier.apply(git_repository, proposal)


def test_patch_rejects_file_creation(git_repository) -> None:
    proposal = PatchProposal(
        unified_diff="--- /dev/null\n+++ b/new_file.py\n@@ -0,0 +1 @@\n+print('no')\n",
        rationale="Unsafe creation.",
    )

    with pytest.raises(PatchRejectedError, match="existing files"):
        PatchApplier().prepare(git_repository, proposal)
