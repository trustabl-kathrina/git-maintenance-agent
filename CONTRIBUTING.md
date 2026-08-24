# Contributing

Thanks for improving Git Maintenance Agent.

## Setup

```powershell
uv sync --all-groups
```

Use Python 3.12 or newer. `uv` is the required contributor workflow; the released package remains installable with pip.

## Before Opening A Pull Request

```powershell
uv run ruff check .
uv run mypy src
uv run python -m pytest
uv run gma skills validate
uv run gma eval run
uv build
```

## Safety Expectations

- Do not add arbitrary shell, credential access, automatic writes, or network tools without an explicit design and security review.
- Keep tools deterministic and typed; agents decide when to use tools, not what a tool means.
- New skills must conform to the bundled `SKILL.md` validation rules and include an evaluation case where possible.
- Preserve the explicit consent and approval boundaries.
