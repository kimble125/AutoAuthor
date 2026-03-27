"""네이버 블로그 기획 템플릿 — 네이버 검색 SEO 최적화"""


class NaverBlogTemplate:
    platform = "naver"
    display_name = "네이버 블로그"

    @staticmethod
    def generate_prompt(title: str, keywords: list[dict], content_type: str) -> str:
        golden = [k for k in keywords if k.get("is_golden")][:8]
        kw_text = "\n".join(f"  - {k['keyword']} (점수:{k.get('score',0)})" for k in golden)

        return f"""당신은 네이버 블로그 SEO 전문가입니다.

'{title}' ({content_type}) 네이버 블로그 기획안 2종을 작성하세요.

[황금 키워드]
{kw_text or '  (없음)'}

[네이버 블로그 SEO 규칙]
- 제목 30~45자 (네이버 검색 결과 노출 최적)
- 본문 1,500~2,500자 (네이버 C-rank 알고리즘 선호 길이)
- 사진 3~5장 포함 권장 (alt 텍스트에 키워드)
- 소제목(H3) 3~4개
- 태그(해시태그) 10개 이내
- 첫 문단 100자 이내에 핵심 키워드 2회 이상 자연스럽게 배치
- "서로이웃 추가" CTA 포함

[기획안 구조]
1. 제목
2. 소제목 3~4개 (H3)
3. 각 소제목별 핵심 내용 요약 (2~3문장)
4. 추천 이미지 위치
5. 태그 10개
6. 메타: 예상 글 길이, 타깃 키워드
"""
