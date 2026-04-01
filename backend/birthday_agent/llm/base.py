from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    text: str


class LLMClient:
    def is_configured(self) -> bool:
        raise NotImplementedError

    def complete(self, prompt: str) -> LLMResponse:
        raise NotImplementedError

