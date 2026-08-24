from __future__ import annotations

import pytest

from git_maintenance_agent.models import InvestigationPlan, InvestigationReport, PatchProposal
from git_maintenance_agent.orchestrator import InvestigationService
from git_maintenance_agent.patching import PatchApplier
from git_maintenance_agent.runtime import FakeAgentRuntime
from git_maintenance_agent.skills.registry import SkillRegistry


@pytest.mark.asyncio
async def test_fake_agent_can_propose_then_apply_a_verified_fix(git_repository) -> None:
    (git_repository.root / "maths.py").write_text(
        "def add(left: int, right: int) -> int:\n    return left - right\n", encoding="utf-8"
    )
    tests = git_repository.root / "tests"
    tests.mkdir()
    (tests / "test_maths.py").write_text(
        "from maths import add\n\n\ndef test_add() -> None:\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )
    plan = InvestigationPlan(
        selected_skills=["pytest-debugging", "git-investigation"],
        hypothesis="Addition subtracts its operands.",
        test_target="tests/test_maths.py::test_add",
    )
    patch = PatchProposal(
        unified_diff="""diff --git a/maths.py b/maths.py
index 0000000..1111111 100644
--- a/maths.py
+++ b/maths.py
@@ -1,2 +1,2 @@
 def add(left: int, right: int) -> int:
-    return left - right
+    return left + right
""",
        rationale="Use addition in add().",
    )
    runtime = FakeAgentRuntime(
        plan,
        InvestigationReport(summary="Found the arithmetic bug.", patch=patch, confidence=0.99),
    )
    service = InvestigationService(runtime, SkillRegistry(), PatchApplier())

    report = await service.investigate(
        git_repository,
        "Fix the failing arithmetic test.",
        allow_cloud_analysis=True,
        allow_test_execution=True,
    )

    assert report.patch is not None
    assert report.commands[-1].exit_code == 1
    PatchApplier().apply(git_repository, report.patch)
    assert git_repository.run_pytest(None, approved=True).exit_code == 0
