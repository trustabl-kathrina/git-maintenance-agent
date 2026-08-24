"""The public command-line interface for Git Maintenance Agent."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import Settings
from .errors import GitMaintenanceAgentError
from .evals import run_evaluations
from .models import InvestigationReport
from .orchestrator import InvestigationService
from .patching import PatchApplier
from .runtime import OpenAIAgentRuntime
from .skills.registry import SkillRegistry
from .workspace import Workspace

app = typer.Typer(
    name="gma",
    help="Investigate Python repository failures with portable skills and safe tools.",
    no_args_is_help=True,
)
skills_app = typer.Typer(help="Inspect and validate bundled Agent Skills.", no_args_is_help=True)
eval_app = typer.Typer(help="Run deterministic evaluation-fixture checks.", no_args_is_help=True)
app.add_typer(skills_app, name="skills")
app.add_typer(eval_app, name="eval")
console = Console()


def _fail(error: Exception | str) -> None:
    console.print(f"[red]Error:[/red] {error}")
    raise typer.Exit(code=2)


def _render_report(report: InvestigationReport) -> None:
    console.print(Panel.fit(report.summary, title="Git Maintenance Agent"))
    if report.selected_skills:
        console.print(f"[bold]Skills:[/bold] {', '.join(report.selected_skills)}")
    if report.findings:
        table = Table("Severity", "Location", "Finding", "Suggested fix")
        for finding in report.findings:
            location = ""
            if finding.location:
                location = finding.location.path
                if finding.location.line:
                    location += f":{finding.location.line}"
            table.add_row(
                finding.severity.value, location, finding.title, finding.suggested_fix or ""
            )
        console.print(table)
    if report.patch:
        console.print(
            Panel(report.patch.unified_diff, title="Proposed patch", border_style="yellow")
        )
    if report.limitations:
        console.print("[yellow]Limitations:[/yellow] " + "; ".join(report.limitations))


@app.command()
def investigate(
    repository: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    task: str = typer.Option(..., "--task", help="Maintenance goal to investigate."),
    allow_cloud_analysis: bool = typer.Option(
        False,
        "--allow-cloud-analysis",
        help="Authorize sending safe repository evidence to OpenAI.",
    ),
    allow_test_execution: bool = typer.Option(
        False,
        "--allow-test-execution",
        help="Authorize local pytest execution in the target repository.",
    ),
    apply: bool = typer.Option(
        False, "--apply", help="Offer to apply a proposed patch after confirmation."
    ),
    model: str | None = typer.Option(None, "--model", help="Override GMA_MODEL for this run."),
    output_format: Literal["terminal", "json"] = typer.Option("terminal", "--format"),
    report_path: Path | None = typer.Option(
        None, "--report", help="Write the JSON report to this path."
    ),
) -> None:
    """Investigate a Git repository without writing unless --apply is confirmed."""

    try:
        settings = Settings.from_environment()
        if model:
            settings = Settings(
                api_key=settings.api_key, model=model, reasoning_effort=settings.reasoning_effort
            )
        workspace = Workspace.open(repository)
        runtime = OpenAIAgentRuntime(settings)
        service = InvestigationService(runtime, SkillRegistry(), PatchApplier())
        report = asyncio.run(
            service.investigate(
                workspace,
                task,
                allow_cloud_analysis=allow_cloud_analysis,
                allow_test_execution=allow_test_execution,
            )
        )
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        if output_format == "json":
            typer.echo(report.model_dump_json(indent=2))
        else:
            _render_report(report)
        if apply and report.patch:
            if typer.confirm("Apply this patch to the current worktree?", default=False):
                PatchApplier().apply(workspace, report.patch)
                console.print("[green]Patch applied. No commit was created.[/green]")
            else:
                console.print("Patch was not applied.")
    except GitMaintenanceAgentError as error:
        _fail(error)


@app.command()
def doctor(
    repository: Path | None = typer.Option(
        None, "--repository", help="Optionally check a repository path."
    ),
) -> None:
    """Report local readiness without exposing credentials or making network calls."""

    settings = Settings.from_environment()
    checks: list[tuple[str, str, str]] = []
    checks.append(
        (
            "Python",
            f"{sys.version_info.major}.{sys.version_info.minor}",
            "ok" if sys.version_info >= (3, 12) else "fail",
        )
    )
    checks.append(
        (
            "OPENAI_API_KEY",
            "configured" if settings.api_key else "missing",
            "ok" if settings.api_key else "fail",
        )
    )
    model_ok = bool(settings.model.strip()) and " " not in settings.model
    checks.append(
        ("Model", settings.model if model_ok else "invalid", "ok" if model_ok else "fail")
    )
    target = repository or Path.cwd()
    try:
        workspace = Workspace.open(target)
        checks.append(("Git repository", str(workspace.root), "ok"))
    except GitMaintenanceAgentError:
        checks.append(("Git repository", "not found", "fail"))
    table = Table("Check", "Status", "Result")
    for name, status, result in checks:
        table.add_row(
            name, status, "[green]ready[/green]" if result == "ok" else "[red]action needed[/red]"
        )
    console.print(table)
    if not settings.api_key:
        console.print(
            "Set OPENAI_API_KEY from your OpenAI API Platform project before running `gma investigate`."
        )
    if any(result == "fail" for _, _, result in checks):
        raise typer.Exit(code=1)


@skills_app.command("list")
def list_skills() -> None:
    """List metadata without loading full skill instructions."""

    table = Table("Name", "Description")
    for skill in SkillRegistry().discover():
        table.add_row(skill.name, skill.description)
    console.print(table)


@skills_app.command("validate")
def validate_skills() -> None:
    """Validate bundled SKILL.md files against the project's portable subset."""

    errors = SkillRegistry().validate()
    if errors:
        for error in errors:
            console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1)
    console.print("[green]All bundled skills are valid.[/green]")


@eval_app.command("run")
def run_eval(case_directory: Path = typer.Option(Path("evals/cases"), "--cases")) -> None:
    """Validate deterministic evaluation fixtures without calling a model."""

    if not case_directory.is_dir():
        _fail(f"Evaluation case directory does not exist: {case_directory}")
    results = run_evaluations(case_directory, SkillRegistry())
    table = Table("Case", "Result", "Message")
    for result in results:
        table.add_row(
            result.case_id,
            "[green]pass[/green]" if result.passed else "[red]fail[/red]",
            result.message,
        )
    console.print(table)
    if not results or any(not result.passed for result in results):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
