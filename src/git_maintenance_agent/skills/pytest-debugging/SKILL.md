---
name: pytest-debugging
description: Diagnose failing Python pytest suites using the smallest relevant test scope, traceback evidence, and a verified hypothesis. Use when pytest tests fail or regress after a code change.
license: Apache-2.0
---

# Pytest Debugging

1. Run the smallest applicable pytest node id before escalating to the full suite.
2. Capture the failure type, assertion, and first project-owned traceback frame.
3. Inspect the failing test and implementation together; do not infer behavior from the test name alone.
4. Search for call sites, related validation, and boundary conditions that could reproduce the failure.
5. Form one evidence-backed hypothesis at a time and state what would falsify it.
6. Propose only a minimal text patch that preserves existing public behavior outside the defect.
7. After a caller approves a patch, rerun the affected test and report any remaining suite-level risk.

## Guardrails

- Treat a passing targeted test as evidence, not proof that the full suite passes.
- Do not modify fixtures, tests, or production code solely to silence an assertion without explaining the intended behavior.
- Record test commands and output limitations in the final report.
