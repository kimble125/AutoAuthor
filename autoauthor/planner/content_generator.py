"""autoauthor/planner/content_generator.py — AI 기획안 생성기
템플릿 + AI 엔진 체인을 결합하여 멀티플랫폼 기획안을 생성합니다.
"""
from typing import Optional, Union
from ..ai.engine_chain import AIEngineChain
from .templates import PLATFORM_TEMPLATES


class ContentGenerator:
    def __init__(self, ai_chain: AIEngineChain):
        self.ai = ai_chain

    async def generate_plan(
        self,
        title: str,
        content_type: str,
        keywords: list[dict],
        platform: str = "tistory",
    ) -> dict:
        """단일 플랫폼 기획안 생성"""
        template_cls = PLATFORM_TEMPLATES.get(platform)
        if not template_cls:
            raise ValueError(f"지원하지 않는 플랫폼: {platform}. 가능: {list(PLATFORM_TEMPLATES.keys())}")

        prompt = template_cls.generate_prompt(title, keywords, content_type)

        system = (
            "당신은 한국 콘텐츠 마케팅 전문가입니다. "
            "SEO 최적화와 독자 유입을 극대화하는 기획안을 작성합니다. "
            "반드시 한국어로 답변하세요."
        )

        response = await self.ai.generate(
            prompt=prompt,
            system_prompt=system,
            temperature=0.7,
            max_tokens=4096,
        )

        return {
            "platform": platform,
            "platform_display": template_cls.display_name,
            "title": title,
            "content_type": content_type,
            "plan_text": response.text,
            "ai_model": response.model,
            "tokens_used": response.tokens_used,
            "fallback_used": response.fallback_used,
        }

    async def generate_multi_platform(
        self,
        title: str,
        content_type: str,
        keywords: list[dict],
        platforms: Optional[list[str]] = None,
    ) -> list[dict]:
        """여러 플랫폼 기획안 일괄 생성"""
        if platforms is None:
            platforms = ["tistory"]

        results = []
        for pf in platforms:
            try:
                plan = await self.generate_plan(title, content_type, keywords, pf)
                results.append(plan)
                print(f"  ✅ {pf} 기획안 생성 완료 (model: {plan['ai_model']})")
            except Exception as e:
                print(f"  ⚠️ {pf} 기획안 생성 실패: {e}")
                results.append({"platform": pf, "error": str(e)})

        return results
