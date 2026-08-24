from __future__ import annotations

from typer.testing import CliRunner

from git_maintenance_agent.cli import app


def test_doctor_reports_configured_local_prerequisites(git_repository, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = CliRunner().invoke(app, ["doctor", "--repository", str(git_repository.root)])

    assert result.exit_code == 0
    assert "configured" in result.stdout
    assert "test-key" not in result.stdout


def test_investigate_requires_explicit_cloud_consent(git_repository, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = CliRunner().invoke(
        app,
        ["investigate", str(git_repository.root), "--task", "Find a failure"],
    )

    assert result.exit_code == 2
    assert "allow-cloud-analysis" in result.stdout
