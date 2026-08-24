"""Discovery and validation for progressive Agent Skills loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..errors import GitMaintenanceAgentError


@dataclass(frozen=True, slots=True)
class SkillSummary:
    """Startup-safe metadata used for skill selection."""

    name: str
    description: str
    path: Path


@dataclass(frozen=True, slots=True)
class Skill:
    """A fully activated skill with procedure content."""

    summary: SkillSummary
    instructions: str


class SkillRegistry:
    """Loads only frontmatter until a selected skill needs activation."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(__file__).parent

    def discover(self) -> list[SkillSummary]:
        summaries: list[SkillSummary] = []
        for document in sorted(self._root.glob("*/SKILL.md")):
            summaries.append(self._parse_summary(document))
        return summaries

    def load(self, names: list[str]) -> list[Skill]:
        summaries = {summary.name: summary for summary in self.discover()}
        missing = sorted(set(names) - summaries.keys())
        if missing:
            raise GitMaintenanceAgentError(f"Unknown skill(s): {', '.join(missing)}")
        return [self._load_skill(summaries[name]) for name in names]

    def validate(self) -> list[str]:
        errors: list[str] = []
        for document in sorted(self._root.glob("*/SKILL.md")):
            try:
                skill = self._load_skill(self._parse_summary(document))
                if len(skill.instructions.splitlines()) > 500:
                    errors.append(f"{document}: instructions exceed 500 lines")
            except (GitMaintenanceAgentError, yaml.YAMLError) as error:
                errors.append(f"{document}: {error}")
        return errors

    def _parse_summary(self, document: Path) -> SkillSummary:
        metadata, _ = self._parse_document(document)
        name = metadata.get("name")
        description = metadata.get("description")
        if not isinstance(name, str) or not name:
            raise GitMaintenanceAgentError("Skill frontmatter requires a non-empty name.")
        if name != document.parent.name:
            raise GitMaintenanceAgentError("Skill name must match its directory name.")
        if not isinstance(description, str) or not description:
            raise GitMaintenanceAgentError("Skill frontmatter requires a non-empty description.")
        if len(name) > 64 or not all(
            character.islower() or character.isdigit() or character == "-" for character in name
        ):
            raise GitMaintenanceAgentError(
                "Skill name must use lowercase letters, digits, and hyphens only."
            )
        return SkillSummary(name=name, description=description, path=document)

    def _load_skill(self, summary: SkillSummary) -> Skill:
        _, instructions = self._parse_document(summary.path)
        if not instructions.strip():
            raise GitMaintenanceAgentError("Skill instructions cannot be empty.")
        return Skill(summary=summary, instructions=instructions.strip())

    @staticmethod
    def _parse_document(document: Path) -> tuple[dict[str, object], str]:
        raw = document.read_text(encoding="utf-8")
        if not raw.startswith("---\n"):
            raise GitMaintenanceAgentError("SKILL.md must begin with YAML frontmatter.")
        try:
            _, frontmatter, body = raw.split("---\n", 2)
        except ValueError as error:
            raise GitMaintenanceAgentError("SKILL.md frontmatter is not closed.") from error
        metadata = yaml.safe_load(frontmatter)
        if not isinstance(metadata, dict):
            raise GitMaintenanceAgentError("Skill frontmatter must be a YAML mapping.")
        return metadata, body
