# Low-Level Design

## Package Layout

`src/git_maintenance_agent` contains the CLI, configuration, models, workspace safety layer, typed tools, skill registry, runtime adapter, orchestrator, patch applier, and offline evaluation runner.

## Public Contracts

`InvestigationPlan` selects one to three skill names, states a hypothesis, and may target a pytest node id. `InvestigationReport` contains findings, evidence, command results, selected skills, an optional `PatchProposal`, confidence, and limitations. These Pydantic models are the JSON output schema.

## Tool Contracts

The agent may call `read_file`, `list_files`, `search_code`, `git_status`, `git_diff`, `git_log`, and `run_pytest`. Each tool is a deterministic Python operation with path checks, timeout bounds, output truncation, and no shell interpolation. `run_pytest` fails unless the CLI command included `--allow-test-execution`.

## Skill Lifecycle

1. `SkillRegistry.discover()` reads only YAML `name` and `description` fields.
2. The planner chooses at most three known names.
3. `SkillRegistry.load()` reads only those instruction bodies.
4. The investigator receives selected instructions and constrained tool functions.

## Patch Lifecycle

1. Model output supplies a unified diff and rationale.
2. The local patch applier accepts only modifications to existing `a/path` and `b/path` text files.
3. It snapshots SHA-256 hashes before rendering the report.
4. At approval time it checks hashes, runs `git apply --check`, then invokes `git apply`.
5. The CLI never creates a commit.
