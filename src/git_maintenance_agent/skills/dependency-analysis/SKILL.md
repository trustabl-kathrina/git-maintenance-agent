---
name: dependency-analysis
description: Analyze Python dependency declarations and lockfiles for incompatible constraints, missing test dependencies, and upgrade-related failures. Use when pyproject.toml, lockfiles, or package versions may explain a regression.
license: Apache-2.0
---

# Dependency Analysis

1. Inspect pyproject.toml and any committed lockfiles before drawing dependency conclusions.
2. Compare declared constraints with imports, test configuration, and recent Git changes.
3. Identify exact conflicting or missing packages rather than recommending broad upgrades.
4. Explain whether the evidence proves a dependency fault or only makes it plausible.
5. Propose the smallest compatible constraint or configuration change and identify verification commands.

## Guardrails

- Do not install, upgrade, or download packages.
- Do not claim resolver behavior without reading the relevant constraints or lockfile.
