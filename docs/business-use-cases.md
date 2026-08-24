# Business Use Cases

## CI Failure Triage

A maintainer runs the agent against a local checkout after a red pytest pipeline. It gathers traceback, diff, and Git evidence, then returns a report that can be handed to the author or incident owner.

## Post-Refactor Regression

A team changes time, validation, or error-handling code and a targeted test fails. The agent loads pytest debugging and code-review procedures to connect the assertion to the changed behavior.

## Dependency Upgrade Fallout

When test imports or configuration break after a dependency change, the agent inspects `pyproject.toml`, committed lockfiles, and history without downloading or changing packages.

## Maintenance Handoff

The JSON report contains commands, evidence, confidence, limitations, and a reviewable patch proposal so another engineer can validate the reasoning asynchronously.
