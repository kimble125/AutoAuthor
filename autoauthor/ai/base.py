"""autoauthor/ai/base.py"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    text: str
    model: str
    tokens_used: int = 0
    cost_estimate: float = 0.0
    fallback_used: bool = False


class BaseAIEngine(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.7, max_tokens: int = 4096,
                       json_mode: bool = False) -> AIResponse:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass
