"""스레드/X(트위터) 포스트 기획 템플릿"""


class ThreadXTemplate:
    platform = "thread"
    display_name = "스레드/X 포스트"

    @staticmethod
    def generate_prompt(title: str, keywords: list[dict], content_type: str) -> str:
        kw_text = "\n".join(f"  - {k['keyword']}" for k in keywords[:6])

        return f"""당신은 X(트위터)/스레드 바이럴 전문가입니다.

'{title}' ({content_type}) 관련 스레드(5~8개 트윗)를 기획하세요.

[연관 키워드]
{kw_text}

[스레드 구조]
- 트윗1: 훅 (논쟁적 의견 or 놀라운 사실 → 리트윗 유도)
- 트윗2~6: 본론 (1트윗 = 1포인트, 280자 이내)
- 트윗7: 요약/결론
- 트윗8: CTA ("리트윗해서 공유해주세요" + 팔로우 유도)

[각 트윗마다]
1. 트윗 번호
2. 텍스트 (280자 이내, 줄바꿈 활용)
3. 이미지 첨부 여부 (Y/N + 이미지 설명)

[바이럴 규칙]
- 첫 트윗에 숫자 or 강한 주장 포함
- 매 트윗 줄바꿈으로 가독성 확보
- 이미지는 트윗2, 트윗5에 배치 (시선 분산 방지)
- 마지막에 원문 블로그 링크 자연스럽게 포함

[추가로]
- 단독 트윗(스레드 아닌) 버전 1개도 작성 (280자 이내, 블로그 유입용)
"""
