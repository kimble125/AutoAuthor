"""autoauthor/ai/ollama_engine.py — Ollama 로컬 LLM (EXAONE 3.5, Qwen2.5)"""
import aiohttp
from .base import BaseAIEngine, AIResponse


class OllamaEngine(BaseAIEngine):
    name = "ollama"

    def __init__(self, model: str = "exaone3.5:7.8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def generate(self, prompt, system_prompt="", temperature=0.7,
                       max_tokens=4096, json_mode=False) -> AIResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"

        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.base_url}/api/generate", json=payload,
                              timeout=aiohttp.ClientTimeout(total=120)) as r:
                data = await r.json()

        return AIResponse(
            text=data.get("response", ""),
            model=self.model,
            tokens_used=data.get("eval_count", 0),
            cost_estimate=0.0,
        )

    async def is_available(self) -> bool:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{self.base_url}/api/tags",
                                 timeout=aiohttp.ClientTimeout(total=3)) as r:
                    if r.status == 200:
                        data = await r.json()
                        names = [m["name"] for m in data.get("models", [])]
                        return any(self.model.split(":")[0] in n for n in names)
            return False
        except Exception:
            return False
