"""Stable, serializable contracts returned by investigations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Impact level for a repository finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FileReference(BaseModel):
    """A source location that is safe to render in human or JSON reports."""

    path: str
    line: int | None = Field(default=None, ge=1)


class Evidence(BaseModel):
    """Observed repository evidence supporting an investigation result."""

    source: str
    summary: str
    location: FileReference | None = None


class CommandResult(BaseModel):
    """A bounded result from an allowed local command."""

    command: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


class Finding(BaseModel):
    """An actionable, evidence-backed problem in the target repository."""

    severity: Severity
    title: str
    explanation: str
    location: FileReference | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    suggested_fix: str | None = None


class PatchProposal(BaseModel):
    """A candidate text-only patch. Hashes are added locally before application."""

    unified_diff: str
    rationale: str
    target_hashes: dict[str, str] = Field(default_factory=dict)


class InvestigationPlan(BaseModel):
    """The model's constrained skill-selection and evidence-gathering plan."""

    selected_skills: list[str] = Field(min_length=1, max_length=3)
    hypothesis: str
    evidence_queries: list[str] = Field(default_factory=list, max_length=8)
    test_target: str | None = None


class InvestigationReport(BaseModel):
    """The public result of an agent investigation."""

    summary: str
    findings: list[Finding] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    commands: list[CommandResult] = Field(default_factory=list)
    selected_skills: list[str] = Field(default_factory=list)
    patch: PatchProposal | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
