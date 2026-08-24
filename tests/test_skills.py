from __future__ import annotations

from git_maintenance_agent.skills.registry import SkillRegistry


def test_discovers_only_expected_skill_metadata() -> None:
    registry = SkillRegistry()

    summaries = registry.discover()

    assert [summary.name for summary in summaries] == [
        "dependency-analysis",
        "git-investigation",
        "pytest-debugging",
        "python-code-review",
    ]
    assert all(summary.description for summary in summaries)


def test_loads_selected_skill_and_validates_bundle() -> None:
    registry = SkillRegistry()

    skill = registry.load(["pytest-debugging"])[0]

    assert "Run the smallest applicable pytest node id" in skill.instructions
    assert registry.validate() == []
