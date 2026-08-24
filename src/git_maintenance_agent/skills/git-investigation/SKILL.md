---
name: git-investigation
description: Investigate repository history, diffs, and working-tree state to connect regressions with likely code changes. Use when recent commits, uncommitted changes, or blame-worthy history may explain a maintenance issue.
license: Apache-2.0
---

# Git Investigation

1. Inspect working-tree status and the current diff before relying on history.
2. Review recent commit subjects and focused file history related to the reported behavior.
3. Compare changed code against the failing test and relevant implementation paths.
4. Separate correlation from demonstrated causation in the final report.
5. Preserve unrelated user changes and never create, amend, reset, or commit Git history.

## Guardrails

- Use only the exposed read-only Git operations.
- Report when a dirty worktree limits confidence in a proposed patch.
