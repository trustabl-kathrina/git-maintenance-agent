"""OpenAI Agents SDK adapter and deterministic test double."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from .config import Settings
from .errors import RuntimeConfigurationError
from .models import InvestigationPlan, InvestigationReport
from .skills.registry import Skill, SkillSummary
from .tools import RepositoryTools

OutputT = TypeVar("OutputT", InvestigationPlan, InvestigationReport)


class AgentRuntime(Protocol):
    """Boundary that keeps orchestration testable without API calls."""

    async def create_plan(
        self, task: str, skills: list[SkillSummary], repository_context: str
    ) -> InvestigationPlan: ...

    async def investigate(
        self,
        task: str,
        skills: list[Skill],
        repository_context: str,
        tools: RepositoryTools,
    ) -> InvestigationReport: ...


class OpenAIAgentRuntime:
    """A narrow use of the Agents SDK with only safe repository functions."""

    def __init__(self, settings: Settings) -> None:
        if not settings.api_key:
            raise RuntimeConfigurationError(
                "OPENAI_API_KEY is required for a live investigation. Run `gma doctor` for setup help."
            )
        self._settings = settings

    async def create_plan(
        self, task: str, skills: list[SkillSummary], repository_context: str
    ) -> InvestigationPlan:
        Agent, ModelSettings, Runner, _ = self._load_sdk()
        catalog = "\n".join(f"- {skill.name}: {skill.description}" for skill in skills)
        agent = Agent(
            name="Maintenance planner",
            model=self._settings.model,
            instructions=(
                "Select one to three skills from the catalog and return only the required structured plan. "
                "Do not invent skill names. Prefer pytest-debugging for failing Python tests and "
                "git-investigation when repository history may help."
            ),
            model_settings=ModelSettings(
                reasoning={"effort": self._settings.reasoning_effort}, verbosity="low"
            ),
            output_type=InvestigationPlan,
        )
        result = await Runner.run(
            agent,
            f"Task:\n{task}\n\nAvailable skills:\n{catalog}\n\nRepository context:\n{repository_context}",
        )
        return self._coerce_output(result.final_output, InvestigationPlan)

    async def investigate(
        self,
        task: str,
        skills: list[Skill],
        repository_context: str,
        tools: RepositoryTools,
    ) -> InvestigationReport:
        Agent, ModelSettings, Runner, function_tool = self._load_sdk()

        @function_tool  # type: ignore[untyped-decorator]
        def read_file(path: str) -> str:
            """Read a safe UTF-8 file from the target repository."""

            return tools.read_file(path)

        @function_tool  # type: ignore[untyped-decorator]
        def list_files(directory: str = ".") -> list[str]:
            """List safe repository files under a directory."""

            return tools.list_files(directory)

        @function_tool  # type: ignore[untyped-decorator]
        def search_code(query: str) -> list[dict[str, object]]:
            """Search safe repository text files for a case-insensitive query."""

            return tools.search_code(query)

        @function_tool  # type: ignore[untyped-decorator]
        def git_status() -> str:
            """Return the short Git status of the target repository."""

            return tools.git_status().model_dump_json()

        @function_tool  # type: ignore[untyped-decorator]
        def git_diff() -> str:
            """Return the current uncommitted Git diff without external diff drivers."""

            return tools.git_diff().model_dump_json()

        @function_tool  # type: ignore[untyped-decorator]
        def git_log(limit: int = 10) -> str:
            """Return recent Git commits, capped at fifty entries."""

            return tools.git_log(limit).model_dump_json()

        @function_tool  # type: ignore[untyped-decorator]
        def run_pytest(nodeid: str | None = None) -> str:
            """Run pytest only because the CLI caller explicitly approved test execution."""

            return tools.run_pytest(nodeid).model_dump_json()

        skill_instructions = "\n\n".join(
            f"## Skill: {skill.summary.name}\n{skill.instructions}" for skill in skills
        )
        agent = Agent(
            name="Git maintenance investigator",
            model=self._settings.model,
            instructions=(
                "Investigate the requested maintenance task using only your provided tools. "
                "Never claim evidence you did not observe. You may propose a unified diff for existing "
                "text files, but do not imply it has been applied. Return the required structured report.\n\n"
                f"Activated skill procedures:\n{skill_instructions}"
            ),
            tools=[read_file, list_files, search_code, git_status, git_diff, git_log, run_pytest],
            model_settings=ModelSettings(
                reasoning={"effort": self._settings.reasoning_effort}, verbosity="low"
            ),
            output_type=InvestigationReport,
        )
        result = await Runner.run(
            agent,
            f"Task:\n{task}\n\nInitial repository evidence:\n{repository_context}",
        )
        return self._coerce_output(result.final_output, InvestigationReport)

    @staticmethod
    def _load_sdk() -> tuple[Any, Any, Any, Any]:
        try:
            from agents import Agent, ModelSettings, Runner, function_tool
        except ImportError as error:
            raise RuntimeConfigurationError(
                "The OpenAI Agents SDK is unavailable. Reinstall git-maintenance-agent."
            ) from error
        return Agent, ModelSettings, Runner, function_tool

    @staticmethod
    def _coerce_output(value: object, output_type: type[OutputT]) -> OutputT:
        if isinstance(value, output_type):
            return value
        return output_type.model_validate(value)


class FakeAgentRuntime:
    """Injectable runtime used by tests and deterministic evaluation fixtures."""

    def __init__(
        self,
        plan: InvestigationPlan,
        report: InvestigationReport | Callable[..., InvestigationReport] | None = None,
    ) -> None:
        self.plan = plan
        self.report = report or InvestigationReport(
            summary="No live model configured.",
            selected_skills=plan.selected_skills,
            limitations=["fake runtime"],
        )

    async def create_plan(
        self, task: str, skills: list[SkillSummary], repository_context: str
    ) -> InvestigationPlan:
        return self.plan

    async def investigate(
        self,
        task: str,
        skills: list[Skill],
        repository_context: str,
        tools: RepositoryTools,
    ) -> InvestigationReport:
        if callable(self.report):
            return self.report(task, skills, repository_context, tools)
        return self.report
