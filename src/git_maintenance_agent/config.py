"""Environment-backed configuration without persisting secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL = "gpt-5.5"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings read once from the caller's environment."""

    api_key: str | None
    model: str
    reasoning_effort: str

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("GMA_MODEL", DEFAULT_MODEL),
            reasoning_effort=os.getenv("GMA_REASONING_EFFORT", "medium"),
        )
