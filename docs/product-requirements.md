# v0.1 Product Requirements

## Goal

Help a Python maintainer investigate a failing pytest suite using bounded local evidence and a user-owned OpenAI API key.

## Primary Flow

1. The user installs `git-maintenance-agent` from PyPI and sets `OPENAI_API_KEY` locally.
2. The user calls `gma investigate` with explicit cloud-analysis and test-execution consent.
3. The agent selects up to three skills, runs only constrained repository tools, and returns a typed report.
4. The user reviews the proposed diff. If `--apply` was supplied, the CLI requests final terminal approval before applying it.

## Non-Goals

- Hosted accounts, OAuth, billing, shared API keys, or a web UI.
- Pull request creation, Git commits, pushes, resets, deleting files, or automatic patching.
- Arbitrary shell commands, package installs, network tools, Docker isolation, MCP, or multi-agent orchestration.

## Success Criteria

- A user can install a wheel with pip and run `gma --help`.
- A configured user can investigate a local Git worktree without granting write access.
- A proposed patch cannot be applied without both `--apply` and a final confirmation.
- Offline tests and evaluation-fixture validation pass without OpenAI credentials.
