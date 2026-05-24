"""연계 콘텐츠(Synergy) 기획 템플릿"""


class SynergyTemplate:
    platform = "synergy"
    display_name = "연계 시너지 기획"

    @staticmethod
    def generate_prompt(titles: list[str], analyses_by_title: dict, category: str) -> str:
        summary_text = ""
        for title in titles:
            analyses = analyses_by_title.get(title, [])
            golden = [a["keyword"] for a in analyses if a.get("is_golden")][:3]
            summary_text += f"- [{title}]: 주요 키워드({', '.join(golden)})\n"

        return f"""당신은 1인 비즈니스 마케터를 위한 콘텐츠 전략가입니다.
여러 개의 개별 콘텐츠를 하나로 묶어 유입 시너지를 극대화하는 '연계 허브 포스팅' 기획안을 작성하세요.

[분석된 작품 목록 및 핵심 키워드]
{summary_text}

[기획 미션]
1. 위 콘텐츠들을 관통하는 하나의 거대한 '테마'를 선정하세요. (예: "우주 생존 SF", "원작보다 강한 각색", "지금 다시 봐야 할 문제작" 등)
2. 각 콘텐츠의 공통점과 차이점을 독자가 비교해서 읽을 수 있는 섹션을 포함하세요.
3. 각 개별 포스팅으로 독자를 유도할 수 있는 '연결 고리(Internal Linking Strategy)'를 설계하세요.
4. 이 통합 포스팅 자체가 구글/네이버 검색 상단에 걸릴 수 있도록 SEO 최적화된 제목과 구조를 제안하세요.

[기획안 구조]
1. 통합 제목: 독자의 클릭을 유도하는 강력한 메인 타이틀
2. 테마 선정 이유: 왜 이 콘텐츠들이 지금 묶여야 하는가? (검색 수요와 독자 관심 반영)
3. 콘텐츠별 비교 포인트: 관점, 장르, 인물, 결말, 원작, 메시지 등 차별화된 분석
4. 연계 리스트 구성: 각 작품을 어떤 순서와 맥락으로 소개할 것인가?
5. 내부 링크 전략: 독자가 이 글을 읽고 각 개별 포스팅으로 넘어가게 만드는 구체적인 문구/버튼 전략
6. 기대 효과: 체류 시간 증대 및 애드센스 수익 극대화 방안

[톤] 전문가의 통찰력이 느껴지면서도 읽기 쉬운 잡지 기사 같은 톤.
"""
