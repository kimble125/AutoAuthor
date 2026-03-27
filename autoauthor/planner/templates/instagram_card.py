"""인스타그램 카드뉴스 기획 템플릿"""


class InstagramCardTemplate:
    platform = "instagram"
    display_name = "인스타그램 카드뉴스"

    @staticmethod
    def generate_prompt(title: str, keywords: list[dict], content_type: str) -> str:
        kw_text = "\n".join(f"  - {k['keyword']}" for k in keywords[:6])

        return f"""당신은 인스타그램 카드뉴스 전문 에디터입니다.

'{title}' ({content_type}) 카드뉴스 기획안을 작성하세요.

[연관 키워드]
{kw_text}

[카드 구조] (총 5~7장, 1080×1350px 4:5 비율)
- 카드1 (표지): 강렬한 타이틀 + 작품 대표 이미지 컨셉
- 카드2: 핵심 포인트 1 (1카드 = 1메시지, 텍스트 3줄 이내)
- 카드3: 핵심 포인트 2
- 카드4: 핵심 포인트 3
- 카드5: 비하인드/재미요소
- 카드6 (CTA): "저장해두세요!" + 프로필 태그

[각 카드마다 제공할 것]
1. 카드 번호
2. 대제목 (굵은 텍스트, 20자 이내)
3. 본문 텍스트 (3줄 이내)
4. 배경 색상/이미지 컨셉
5. 폰트 스타일 제안

[디자인 가이드]
- 한글 폰트: 프리텐다드 / 나눔스퀘어
- 영문 폰트: Montserrat / Poppins
- 작품 분위기에 맞는 2~3색 팔레트 제안
- Canva 템플릿 활용 가능한 구조

[캡션 + 해시태그]
- 캡션: 3~5줄 (첫 줄에 훅, 마지막에 CTA)
- 해시태그: 15~20개 (대형 + 중형 + 니치 혼합)
"""
