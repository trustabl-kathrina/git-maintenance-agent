"""Offline validation for the versioned evaluation-fixture catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .skills.registry import SkillRegistry


@dataclass(frozen=True, slots=True)
class EvalResult:
    """The deterministic status of one evaluation fixture."""

    case_id: str
    passed: bool
    message: str


def run_evaluations(case_directory: Path, registry: SkillRegistry) -> list[EvalResult]:
    """Validate that each case, its fixture, and referenced skills are present."""

    available_skills = {skill.name for skill in registry.discover()}
    results: list[EvalResult] = []
    for document in sorted(case_directory.glob("*.yaml")):
        data = yaml.safe_load(document.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            results.append(EvalResult(document.stem, False, "case must contain a YAML mapping"))
            continue
        case_id = data.get("id", document.stem)
        fixture = data.get("fixture")
        expected_skills = data.get("expected_skills", [])
        if (
            not isinstance(case_id, str)
            or not isinstance(fixture, str)
            or not isinstance(expected_skills, list)
        ):
            results.append(EvalResult(document.stem, False, "case has invalid required fields"))
            continue
        fixture_path = case_directory.parent / "fixtures" / fixture
        missing_skills = set(expected_skills) - available_skills
        if not fixture_path.is_dir():
            results.append(EvalResult(case_id, False, f"missing fixture: {fixture}"))
        elif missing_skills:
            results.append(
                EvalResult(case_id, False, f"unknown skills: {', '.join(sorted(missing_skills))}")
            )
        else:
            results.append(EvalResult(case_id, True, "fixture catalog is valid"))
    return results
