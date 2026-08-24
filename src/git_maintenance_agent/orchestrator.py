"""Single-agent investigation lifecycle with explicit consent and typed evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ConsentRequiredError, GitMaintenanceAgentError
from .models import CommandResult, InvestigationReport
from .patching import PatchApplier
from .runtime import AgentRuntime
from .skills.registry import SkillRegistry
from .tools import RepositoryTools
from .workspace import Workspace


@dataclass(slots=True)
class InvestigationService:
    """Coordinates progressive skills, safe tools, and the model runtime."""

    runtime: AgentRuntime
    registry: SkillRegistry
    patch_applier: PatchApplier

    async def investigate(
        self,
        workspace: Workspace,
        task: str,
        *,
        allow_cloud_analysis: bool,
        allow_test_execution: bool,
    ) -> InvestigationReport:
        """Produce a report without mutating the repository."""

        if not allow_cloud_analysis:
            raise ConsentRequiredError(
                "Pass --allow-cloud-analysis before repository evidence is sent to OpenAI."
            )
        catalog = self.registry.discover()
        tools = RepositoryTools(workspace, allow_test_execution=allow_test_execution)
        initial_commands = [tools.git_status(), tools.git_diff()]
        repository_context = self._repository_context(initial_commands)
        plan = await self.runtime.create_plan(task, catalog, repository_context)
        known_names = {summary.name for summary in catalog}
        selected = [name for name in plan.selected_skills if name in known_names]
        if not selected:
            raise GitMaintenanceAgentError("The runtime selected no known skills.")
        skills = self.registry.load(selected)
        if allow_test_execution:
            initial_commands.append(tools.run_pytest(plan.test_target))
            repository_context = self._repository_context(initial_commands)
        report = await self.runtime.investigate(task, skills, repository_context, tools)
        report.selected_skills = selected
        report.commands = [*initial_commands, *report.commands]
        if report.patch:
            report.patch = self.patch_applier.prepare(workspace, report.patch)
        return report

    @staticmethod
    def _repository_context(commands: list[CommandResult]) -> str:
        return "\n\n".join(
            f"Command: {' '.join(command.command)}\nExit: {command.exit_code}\n"
            f"stdout:\n{command.stdout}\nstderr:\n{command.stderr}"
            for command in commands
        )
