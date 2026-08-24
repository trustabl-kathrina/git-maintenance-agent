# Git Maintenance Agent

`git-maintenance-agent` is a Python-first CLI agent that investigates failing pytest suites in local Git repositories. It progressively loads portable Agent Skills, gathers bounded repository evidence, proposes a unified diff, and applies it only after an explicit terminal approval.

## Install

```powershell
pip install git-maintenance-agent
```

Contributors use `uv`; package users do not need it.

## Use Your Own API Key

The package is free, but live investigations use your OpenAI API account and API key. You do not sign in to a service operated by this project, and this project does not collect, proxy, or persist credentials.

1. Create an API key in the [OpenAI API Platform](https://platform.openai.com/api-keys).
2. Configure API billing or credits in that account as needed.
3. Set the key only in your local shell:

```powershell
$env:OPENAI_API_KEY = "your_api_key"
gma doctor --repository .
```

The default model is `gpt-5.5`. Override it with `GMA_MODEL` or `--model`.

## Quick Start

```powershell
gma investigate . `
  --task "Find and fix the failing tests" `
  --allow-cloud-analysis `
  --allow-test-execution
```

The two consent flags are deliberately separate:

- `--allow-cloud-analysis` authorizes sending safe, bounded repository evidence to OpenAI.
- `--allow-test-execution` authorizes local `pytest` execution. Tests run project code locally.
- `--apply` only offers an interactive `[y/N]` confirmation after a patch proposal is produced.

To save a machine-readable report:

```powershell
gma investigate . --task "Investigate failures" --allow-cloud-analysis --allow-test-execution `
  --format json --report investigation.json
```

## Commands

```text
gma doctor [--repository PATH]
gma investigate REPOSITORY --task TEXT --allow-cloud-analysis --allow-test-execution [--apply]
gma skills list
gma skills validate
gma eval run
```

## Safety Model

- Tools have no arbitrary shell or network capability.
- The agent cannot read `.git`, environment files, credential-like files, private keys, or binaries.
- Tool output is capped before it reaches the model.
- Patches can modify only existing text files inside the selected worktree.
- Every patch is checked for stale file hashes and with `git apply --check` before it can be applied.
- The agent never commits, resets, deletes, or pushes Git history.

This is an alpha project. Treat an agent's analysis and patch proposal as assistance, and review any approved change.

## Architecture

```text
CLI -> consent checks -> single orchestrator -> skill registry -> Agents SDK
                                  |                  |
                                  v                  v
                         typed repository tools   SKILL.md procedures
                                  |
                                  v
                            local Git worktree
```

`gma` uses a single manager agent in v0.1. MCP, Docker isolation, hosted access, GitHub actions, and specialist agents are intentionally deferred. See [the design documents](docs/high-level-design.md).

## Development

```powershell
uv sync --all-groups
uv run ruff check .
uv run mypy src
uv run python -m pytest
uv run gma skills validate
uv run gma eval run
uv build
```

## License

Licensed under the [Apache License 2.0](LICENSE).
