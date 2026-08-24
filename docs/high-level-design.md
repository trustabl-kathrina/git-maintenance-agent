# High-Level Design

## System Boundary

Git Maintenance Agent is a local CLI. The user owns the target worktree, API account, API key, and model costs. The CLI sends only allowed repository evidence and selected skill instructions to the OpenAI API after explicit consent.

## Components

| Component | Responsibility |
| --- | --- |
| CLI | Parses consent, model, output, and patch-application options. |
| Workspace and tools | Confines filesystem and Git operations to one worktree. |
| Skill registry | Discovers lightweight metadata, then loads selected `SKILL.md` bodies. |
| Orchestrator | Runs the single-agent plan and investigation lifecycle. |
| Runtime adapter | Uses the OpenAI Agents SDK in production and a fake runtime in tests. |
| Patch applier | Verifies patch paths, hashes, Git applicability, and confirmation-time safety. |

## Data Flow

```text
user command -> consent gate -> Git evidence -> plan with skill summaries
    -> selected skill bodies + bounded tools -> structured report -> optional approval -> patch apply
```

## Trust Boundaries

- Repository contents and test execution are untrusted.
- Model output is advisory and must pass patch validation before it can change files.
- API keys remain environment variables and are never written to config, reports, traces, or logs.
- Test execution is explicitly user-authorized but is not container-isolated in v0.1.

## Evolution

v0.2 can add Docker isolation and richer fixture evaluation. Later releases may add specialist agents as manager tools and an MCP server after the local tool contracts have proven stable.
