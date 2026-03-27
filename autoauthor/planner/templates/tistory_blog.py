"""티스토리 블로그 기획 템플릿"""


class TistoryBlogTemplate:
    platform = "tistory"
    display_name = "티스토리 블로그"

    @staticmethod
    def generate_prompt(title: str, keywords: list[dict], content_type: str) -> str:
        golden = [k for k in keywords if k.get("is_golden")][:10]
        other = [k for k in keywords if not k.get("is_golden")][:5]
        kw_text = "\n".join(f"  - {k['keyword']} (점수:{k.get('score',0)}, 의도:{k.get('intent','탐색형')})" for k in golden)
        other_text = "\n".join(f"  - {k['keyword']} (점수:{k.get('score',0)})" for k in other)

        return f"""당신은 한국 티스토리 블로그 SEO 전문가이자 콘텐츠 에디터입니다.

'{title}' ({content_type}) 리뷰 기획안 3종을 작성하세요.

[황금 키워드 — 블루/퍼플 오션]
{kw_text or '  (없음)'}

[기타 키워드 — 참고용]
{other_text or '  (없음)'}

[기획안 구조] (각 기획안마다)
1. 제목: 40~65자. 핵심 키워드를 앞 20자 이내에 배치.
2. H2 소제목 5개:
   - 들어가며: 독자 호기심 자극하는 질문/상황
   - 본론1: 핵심 분석 포인트
   - 본론2: 심층 해석/비교
   - 본론3: 비하인드/촬영지/OST 등 부가 정보
   - 마치며: 총평 + 별점 + 추천
3. 메타 디스크립션: 150자 이내
4. 태그: 5~10개
5. 예상 글 길이: 2,000~4,000자
6. 타깃 키워드: 3~5개

[차별화]
- 기획안1: 최우선 공략 (최고 기회점수 키워드 조합, 정보형)
- 기획안2: 차별화 각도 (비교형/크로스 키워드)
- 기획안3: 롱테일 (니치 키워드, 매니아 타깃)

[톤] 전문적이면서도 친근한 블로그 톤. 과도한 감탄사 자제.
"""
