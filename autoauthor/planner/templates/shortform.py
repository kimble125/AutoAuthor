"""숏폼 콘텐츠 (TikTok/Reels/Shorts) 기획 템플릿
네이버웹툰 AI 서비스 기획 인턴 포트폴리오용:
  - 숏폼 네이티브 감각 증명
  - AI 도구 활용 능력 어필 (Runway, CapCut, ElevenLabs)
"""


class ShortformTemplate:
    platform = "shortform"
    display_name = "숏폼 (TikTok/Reels/Shorts)"

    @staticmethod
    def generate_prompt(title: str, keywords: list[dict], content_type: str) -> str:
        kw_text = "\n".join(f"  - {k['keyword']}" for k in keywords[:8])

        return f"""당신은 TikTok/Instagram Reels/YouTube Shorts 숏폼 콘텐츠 전문가입니다.

'{title}' ({content_type})을 소재로 한 숏폼 콘텐츠 기획안 3개를 작성하세요.

[연관 키워드]
{kw_text}

[숏폼 기획안 구조] (각 기획안마다)
1. 컨셉 한줄 (훅)
2. 영상 길이: 15초 / 30초 / 60초 중 택1
3. 초 단위 타임라인:
   - 0~3초: 훅 (시선 잡기 — 충격적 사실, 질문, 강렬한 비주얼)
   - 3~15초: 핵심 정보/장면
   - 15~25초: 반전/디테일/감성
   - 25~30초: CTA (좋아요/팔로우/댓글 유도)
4. 화면 자막 텍스트 (실제 화면에 표시될 텍스트)
5. 나레이션/보이스오버 스크립트
6. BGM 분위기 (장르 + 템포)
7. AI 도구 활용 계획:
   - 영상 생성: Runway Gen-4 / Kling AI
   - 음성 합성: ElevenLabs TTS
   - 자동 편집: CapCut 자동자막
   - 이미지 생성: Midjourney / DALL-E 3
8. 해시태그 10개 (트렌드 + 니치 혼합)
9. 최적 업로드 시간대 (한국 기준)

[3종 차별화 전략]
- 기획안1 (정보형): 해석/분석/비교 — "이거 알면 다시 볼 수밖에"
- 기획안2 (감성형): 명대사/명장면/OST — 감정 자극
- 기획안3 (밈형): 트렌드 밈 + 작품 매시업 — 바이럴 최적화

[알고리즘 최적화 팁도 포함]
- 첫 1초에 움직임/텍스트 변화 필수
- 루프 가능한 구조 우대
- 댓글 유도 질문으로 인게이지먼트 확보
"""
