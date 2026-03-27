"""autoauthor/ai/gemini_engine.py"""
from .base import BaseAIEngine, AIResponse


class GeminiEngine(BaseAIEngine):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt, system_prompt="", temperature=0.7,
                       max_tokens=4096, json_mode=False) -> AIResponse:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel(
            self.model,
            system_instruction=system_prompt or None,
        )
        config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else None,
        )

        response = model.generate_content(prompt, generation_config=config)
        usage = getattr(response, 'usage_metadata', None)
        tokens_used = getattr(usage, 'total_token_count', 0) if usage else 0
        return AIResponse(
            text=response.text,
            model=self.model,
            tokens_used=tokens_used,
        )

    async def is_available(self) -> bool:
        return bool(self.api_key)
