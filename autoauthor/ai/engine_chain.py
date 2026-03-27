"""autoauthor/ai/engine_chain.py — AI 엔진 자동 폴백 체인
Gemini Flash → Gemini Flash Lite → Ollama EXAONE → Ollama Qwen2.5
"""
from typing import Optional
from .base import BaseAIEngine, AIResponse
from .gemini_engine import GeminiEngine
from .ollama_engine import OllamaEngine


class AIEngineChain:
    def __init__(self, engines: list[BaseAIEngine]):
        self.engines = engines
        self.last_used: Optional[str] = None

    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        errors = []
        for engine in self.engines:
            if not await engine.is_available():
                continue
            try:
                resp = await engine.generate(prompt, **kwargs)
                if resp.text.strip():
                    self.last_used = engine.name
                    resp.fallback_used = (engine != self.engines[0])
                    return resp
            except Exception as e:
                errors.append(f"{engine.name}({getattr(engine, 'model', '')}): {e}")
                print(f"  ⚠️ {engine.name} 실패 → 다음 엔진")
                continue

        raise RuntimeError("모든 AI 엔진 실패:\n" + "\n".join(errors))


def create_default_chain(gemini_api_key: str = "",
                         ollama_url: str = "http://localhost:11434") -> AIEngineChain:
    engines: list[BaseAIEngine] = []
    if gemini_api_key:
        engines.append(GeminiEngine(gemini_api_key, "gemini-2.5-flash"))
        engines.append(GeminiEngine(gemini_api_key, "gemini-2.5-flash-lite"))
    engines.append(OllamaEngine("exaone3.5:7.8b", ollama_url))
    engines.append(OllamaEngine("qwen2.5:7b-instruct", ollama_url))
    return AIEngineChain(engines)
