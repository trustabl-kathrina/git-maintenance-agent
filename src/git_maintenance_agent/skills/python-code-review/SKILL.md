---
name: python-code-review
description: Review Python changes for correctness, maintainability, typing, error handling, and test risk. Use when a Git diff, patch, or changed Python implementation needs an evidence-backed review.
license: Apache-2.0
---

# Python Code Review

1. Read the Git diff and identify the intended behavioral change.
2. Inspect affected Python call sites, types, tests, and exception paths.
3. Prioritize correctness, data-loss risk, security boundaries, and behavioral regressions over style observations.
4. State each finding with a file location and evidence from the repository.
5. Distinguish confirmed defects from follow-up questions and testing gaps.
6. Suggest focused changes only when they preserve the stated intent.

## Guardrails

- Do not report style preferences as correctness defects.
- Avoid claims about uninspected code or tests.
- Never expose sensitive files or secrets in findings.
