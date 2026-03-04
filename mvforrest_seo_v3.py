"""
==============================================================================
MVforrest SEO 키워드 분석기 V3
==============================================================================
V2 대비 변경 사항:
  - AI 엔진: OpenAI → Google Gemini (google-generativeai 패키지)
  - 기본 모델: gemini-2.5-pro (최고 품질, 한국어 추론 최상위)
  - 모델 선택 옵션 추가: 품질/속도/비용 트레이드오프 설명 포함
  - 크로스 키워드 모드 추가: 여러 작품·이슈를 조합한 키워드 발굴
  - 제목 생성 프롬프트 강화: MVforrest 블로그 스타일 반영

설치:
  pip install requests beautifulsoup4 google-generativeai

Gemini API 키 발급:
  https://aistudio.google.com → Get API key → Create API key
  (Google One 유료 구독자는 더 높은 무료 사용량 한도 적용)

Gemini 모델별 비용 (2026년 2월 기준, 입력 1M 토큰 기준):
  gemini-2.5-pro         : $1.25 (128K 이하) / $2.50 (128K 초과) ← 권장
  gemini-2.5-flash       : $0.15 (128K 이하) / $0.60 (128K 초과)
  gemini-2.5-flash-lite  : $0.10 (128K 이하) / 매우 저렴
  → 1회 분석(키워드 50개 + 제목 생성) 기준 약 $0.001~0.005 (1~7원)
==============================================================================
"""

import argparse
import importlib.util
import random
import requests
import sys
import time
import csv
import os
import json
import re
import math
from datetime import datetime
from urllib.parse import quote
from typing import Optional
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────────────────────────────────────
# [CONFIG] 여기만 수정하면 됩니다
# ──────────────────────────────────────────────────────────────────────────────

# ── 기본 분석 설정 ────────────────────────────────────────────────────────────

# 분석할 시드 키워드 목록 (리뷰 쓸 작품명을 여기에 입력)
SEED_KEYWORDS = [
    "영화 1987",
    "그것이 알고싶다 1477화",
    "계엄",
    "휴민트",
]

# 연관 검색어 탐색 깊이
# 1 = 시드 키워드 자동완성만 / 2 = 2단계 롱테일 확장 (권장)
SEARCH_DEPTH = 2

# 키워드 단어 수 범위 (2~6 권장)
MIN_WORDS = 2
MAX_WORDS = 6

# 요청 간격 (초) — 너무 빠르면 차단될 수 있습니다
REQUEST_DELAY = 0.8

# 결과 저장 폴더
OUTPUT_DIR = "output_preview"

NAVER_CLIENT_ID = ""
NAVER_CLIENT_SECRET = ""
USE_NAVER_OPENAPI = True

CONFIG_ORIGIN: Optional[str] = None

# ── Gemini API 설정 ───────────────────────────────────────────────────────────

# Gemini API 키
# → https://aistudio.google.com → Get API key → Create API key
# → 사용하지 않으려면 빈 문자열("") 로 두세요
GEMINI_API_KEY = ""

# 사용할 Gemini 모델 선택
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  모델명                  │ 한국어 품질 │ 속도  │ 비용  │ 추천 용도       │
# ├─────────────────────────────────────────────────────────────────────────┤
# │  gemini-2.5-pro          │   ★★★★★   │ 보통  │ 중간  │ 최고 품질 필요시│ ← 기본값
# │  gemini-2.5-flash        │   ★★★★☆   │ 빠름  │ 저렴  │ 일반 사용       │
# │  gemini-2.5-flash-lite   │   ★★★☆☆   │ 매우빠름│ 매우저렴│ 대량 처리    │
# └─────────────────────────────────────────────────────────────────────────┘
GEMINI_MODEL = "gemini-2.5-pro"

try:
    import mvforrest_seo_config as _config

    _spec = importlib.util.find_spec("mvforrest_seo_config")
    CONFIG_ORIGIN = getattr(_spec, "origin", None) if _spec else None

    NAVER_CLIENT_ID = getattr(_config, "NAVER_CLIENT_ID", NAVER_CLIENT_ID)
    NAVER_CLIENT_SECRET = getattr(_config, "NAVER_CLIENT_SECRET", NAVER_CLIENT_SECRET)
    USE_NAVER_OPENAPI = getattr(_config, "USE_NAVER_OPENAPI", USE_NAVER_OPENAPI)

    GEMINI_API_KEY = getattr(_config, "GEMINI_API_KEY", GEMINI_API_KEY)
    GEMINI_MODEL = getattr(_config, "GEMINI_MODEL", GEMINI_MODEL)
except Exception as e:
    spec = importlib.util.find_spec("mvforrest_seo_config")
    origin = getattr(spec, "origin", None) if spec else None
    CONFIG_ORIGIN = origin
    err = str(e)
    if len(err) > 200:
        err = err[:200] + "..."
    print(
        "[설정 경고] mvforrest_seo_config.py 로딩 실패로 기본값을 사용합니다. "
        f"({type(e).__name__}: {err})"
    )
    if origin:
        print(f"[설정 경고] 탐지된 설정 파일 경로: {origin}")
    else:
        print(
            "[설정 경고] mvforrest_seo_config 모듈을 찾지 못했습니다. "
            "현재 작업 폴더에서 실행 중인지 확인하세요."
        )
    if sys.path:
        print(f"[설정 경고] sys.path[0]: {sys.path[0]}")

# ── 크로스 키워드 모드 설정 ───────────────────────────────────────────────────

# 크로스 키워드 모드 활성화 여부
# True = 여러 작품/이슈를 조합한 키워드 발굴 (아래 CROSS_TOPICS 설정 필요)
# False = 일반 단일 작품 분석 모드
CROSS_MODE = True

# 크로스 키워드 모드: 연결할 주제 쌍 목록
# 형식: [("주제A", "주제B"), ...] — 두 주제를 연결하는 키워드를 자동 탐색
# 예시: 시의성 있는 사회 이슈 + 관련 영화/드라마 조합
CROSS_TOPICS = [
    # ("사회 이슈/트렌드",  "관련 작품/장르"),
    ("계엄", "영화 1987"),
    ("계엄", "그것이 알고싶다 1477화"),
]

# ──────────────────────────────────────────────────────────────────────────────
# [STEP 1] 구글 자동완성 API로 연관 검색어 수집
# ──────────────────────────────────────────────────────────────────────────────

def get_google_suggestions(seed: str) -> list[str]:
    """Google 자동완성 API로 키워드 후보 가져오기 (재시도/백오프 포함)"""
    params = {
        "client": "firefox",
        "hl": "ko",
        "gl": "KR",
        "q": seed,
    }
    max_retries = 3
    base_delay = 0.8
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                "https://suggestqueries.google.com/complete/search",
                params=params,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; mvforrest-seo/1.0)"},
            )
            resp.raise_for_status()
            data = resp.json()
            # 응답 형식: [원본 쿼리, [제안1, 제안2, ...], [], {}]
            suggestions = data[1] if len(data) > 1 else []
            if attempt > 1:
                print(f"✅ 구글 자동완성 재시도 성공 ({seed})")
            return suggestions
        except Exception as e:
            last_err = e
            status = getattr(resp, 'status_code', None)
            # 재시도 대상: 5xx, 429, 타임아웃, 일시 네트워크 오류
            retryable = (
                isinstance(status, int) and (status >= 500 or status == 429) or
                isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError))
            )
            if not retryable or attempt == max_retries:
                print(f"⚠️  구글 자동완성 오류 ({seed}): {e}")
                return []
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.3)
            print(f"⚠️  구글 자동완성 일시 오류 ({seed}) - {attempt}/{max_retries}회 재시도 중... (대기 {delay:.1f}s)")
            time.sleep(delay)
    return []


def collect_keywords_recursive(
    seed_keywords: list[str],
    depth: int,
    min_words: int,
    max_words: int,
) -> dict[str, bool]:
    """
    시드 키워드에서 depth 단계까지 재귀적으로 연관 검색어를 수집합니다.
    Returns: {키워드: 구글 자동완성 등장 여부} 딕셔너리
    """
    all_keywords: dict[str, bool] = {}
    current_batch = list(seed_keywords)

    for current_depth in range(1, depth + 1):
        print(f"\n  [탐색 {current_depth}단계] {len(current_batch)}개 키워드 처리 중...")
        next_batch = []

        for keyword in current_batch:
            suggestions = get_google_suggestions(keyword)
            time.sleep(REQUEST_DELAY)

            for suggestion in suggestions:
                word_count = len(suggestion.split())
                if not (min_words <= word_count <= max_words):
                    continue
                if suggestion in all_keywords:
                    continue
                # 1단계 = 시드에서 바로 나온 연관어 → 강한 수요 신호 (True/O)
                # 2단계 = 2차 확장에서만 나온 키워드 → 약한 수요 신호 (False/X)
                all_keywords[suggestion] = (current_depth == 1)
                if current_depth < depth:
                    next_batch.append(suggestion)

        current_batch = next_batch
        if not next_batch:
            print(f"  → {current_depth}단계에서 더 이상 새 키워드 없음. 탐색 종료.")
            break

    return all_keywords


# ──────────────────────────────────────────────────────────────────────────────
# [STEP 1-B] 크로스 키워드 모드: 여러 작품/이슈 조합 키워드 수집
# ──────────────────────────────────────────────────────────────────────────────

def collect_cross_keywords(cross_topics: list[tuple[str, str]]) -> dict[str, bool]:
    """
    두 주제를 조합한 크로스 키워드를 수집합니다.

    전략:
    1. 각 주제 쌍의 조합 쿼리로 구글 자동완성 호출
    2. 두 주제를 모두 포함하는 키워드만 필터링
    3. 각 주제의 단독 자동완성 결과도 수집해 교차 분석

    Args:
        cross_topics: [("주제A", "주제B"), ...] 형태의 주제 쌍 목록

    Returns:
        {키워드: True} 딕셔너리 (모든 크로스 키워드)
    """
    cross_keywords: dict[str, bool] = {}

    print(f"\n  [크로스 모드] {len(cross_topics)}개 주제 쌍 분석 중...")

    for topic_a, topic_b in cross_topics:
        print(f"\n  ▶ 조합: '{topic_a}' × '{topic_b}'")

        # 조합 1: "주제A 주제B" 직접 검색
        combined_query = f"{topic_a} {topic_b}"
        suggestions_combined = get_google_suggestions(combined_query)
        time.sleep(REQUEST_DELAY)

        # 조합 2: "주제B 주제A" 역순 검색
        reversed_query = f"{topic_b} {topic_a}"
        suggestions_reversed = get_google_suggestions(reversed_query)
        time.sleep(REQUEST_DELAY)

        # 조합 3: 각 주제의 단독 자동완성에서 상대 주제 포함 키워드 필터링
        suggestions_a = get_google_suggestions(topic_a)
        time.sleep(REQUEST_DELAY)
        suggestions_b = get_google_suggestions(topic_b)
        time.sleep(REQUEST_DELAY)

        # 주제A 자동완성 중 주제B 관련 단어 포함된 것
        cross_from_a = [
            s for s in suggestions_a
            if any(word in s for word in topic_b.split())
        ]
        # 주제B 자동완성 중 주제A 관련 단어 포함된 것
        cross_from_b = [
            s for s in suggestions_b
            if any(word in s for word in topic_a.split())
        ]

        # 수집된 모든 크로스 키워드 합산
        all_cross = (
            suggestions_combined
            + suggestions_reversed
            + cross_from_a
            + cross_from_b
        )

        for kw in all_cross:
            word_count = len(kw.split())
            if 2 <= word_count <= 7:  # 크로스 키워드는 단어 수 범위를 넓게
                cross_keywords[kw] = True
                print(f"    ✓ {kw}")

    print(f"\n  → 크로스 키워드 총 {len(cross_keywords)}개 수집 완료")
    return cross_keywords


# ──────────────────────────────────────────────────────────────────────────────
# [STEP 2] 네이버 경쟁도 측정
# ──────────────────────────────────────────────────────────────────────────────

def get_naver_blog_competition(keyword: str) -> int:
    """네이버 블로그 탭 1페이지 결과 수 (낮을수록 경쟁 적음)"""
    if USE_NAVER_OPENAPI and NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        total = get_naver_openapi_total(search_type="blog", keyword=keyword)
        if total is None:
            pass
        else:
            return convert_total_to_competition(total)
    url = "https://search.naver.com/search.naver"
    params = {"where": "blog", "query": keyword}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".total_wrap") or soup.select(".api_subject_bx")
        return len(items)
    except Exception as e:
        print(f"  ⚠️  네이버 블로그 경쟁도 오류 ({keyword}): {e}")
        return -1


def get_naver_view_competition(keyword: str) -> int:
    """네이버 VIEW 탭 1페이지 결과 수 (블로그+카페 통합)"""
    if USE_NAVER_OPENAPI and NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        total_blog = get_naver_openapi_total(search_type="blog", keyword=keyword)
        total_cafe = get_naver_openapi_total(search_type="cafearticle", keyword=keyword)
        if total_blog is None or total_cafe is None:
            pass
        else:
            return convert_total_to_competition(total_blog + total_cafe)
    url = "https://search.naver.com/search.naver"
    params = {"where": "view", "query": keyword}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = (
            soup.select(".view_wrap")
            or soup.select(".total_wrap")
            or soup.select(".api_subject_bx")
        )
        return len(items)
    except Exception as e:
        print(f"  ⚠️  네이버 VIEW 경쟁도 오류 ({keyword}): {e}")
        return -1


def get_naver_openapi_total(search_type: str, keyword: str) -> Optional[int]:
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": keyword, "display": 1, "start": 1, "sort": "sim"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            msg = resp.text
            if len(msg) > 400:
                msg = msg[:400] + "..."
            print(
                f"  ⚠️  네이버 OpenAPI 오류 ({search_type}, {keyword}): "
                f"HTTP {resp.status_code} | {msg}"
            )
            return None
        data = resp.json()
        total = data.get("total")
        if isinstance(total, int):
            return total
        return None
    except Exception as e:
        print(f"  ⚠️  네이버 OpenAPI 예외 ({search_type}, {keyword}): {e}")
        return None


def convert_total_to_competition(total: int) -> int:
    if total < 0:
        return -1
    if total == 0:
        return 0
    score = int(math.log10(total + 1) * 10)
    return min(50, max(0, score))


# ──────────────────────────────────────────────────────────────────────────────
# [STEP 3] 기회 점수 계산
# ──────────────────────────────────────────────────────────────────────────────

def calculate_opportunity_score(
    has_demand: bool,
    blog_competition: int,
    view_competition: int,
) -> float:
    """
    기회 점수 = (블로그 역수 × 0.6) + (VIEW 역수 × 0.4)
    수요 없으면 × 0.3 패널티 적용
    점수 해석: 50+ 황금 / 20~49 유망 / 10~19 보통 / 10 미만 레드오션
    """
    if blog_competition < 0:
        blog_competition = 10
    if view_competition < 0:
        view_competition = 10

    blog_score = 100 / (blog_competition + 1)
    view_score = 100 / (view_competition + 1)
    combined = (blog_score * 0.6) + (view_score * 0.4)

    if not has_demand:
        combined *= 0.3

    return round(combined, 1)


def classify_keyword(score: float, has_demand: bool) -> str:
    if not has_demand:
        return "수요 불확실"
    if score >= 50:
        return "황금 키워드"
    elif score >= 20:
        return "유망 키워드"
    elif score >= 10:
        return "보통"
    else:
        return "레드오션"


def classify_search_intent(keyword: str) -> str:
    """키워드의 검색 의도를 자동 분류합니다."""
    info_patterns = [
        "정리", "요약", "뜻", "의미", "설명", "이유", "방법", "차이", "비교",
        "줄거리", "결말", "해석", "분석", "리뷰", "후기", "감상", "평가",
        "실화", "배경", "역사", "원작", "원작자", "감독", "출연진", "촬영지",
        "반복", "연결", "관계", "공통점", "차이점",  # 크로스 콘텐츠용 추가
    ]
    transact_patterns = [
        "개봉", "예매", "티켓", "넷플릭스", "왓챠", "디즈니", "쿠팡",
        "다시보기", "무료", "보는법", "어디서",
    ]
    explore_patterns = [
        "추천", "순위", "목록", "리스트", "모음", "시리즈", "OST", "가사",
        "예고편", "클립", "영상", "사진", "포스터",
    ]

    for pattern in info_patterns:
        if pattern in keyword:
            return "정보형"
    for pattern in transact_patterns:
        if pattern in keyword:
            return "거래형"
    for pattern in explore_patterns:
        if pattern in keyword:
            return "탐색형"
    return "탐색형"


# ──────────────────────────────────────────────────────────────────────────────
# [STEP 4] Gemini API 연동 — 블로그 제목 자동 생성
# ──────────────────────────────────────────────────────────────────────────────

def generate_blog_titles_with_gemini(
    golden_keywords: list[dict],
    api_key: str,
    model: str,
    is_cross_mode: bool = False,
    cross_topics: Optional[list[tuple[str, str]]] = None,
) -> str:
    """
    Gemini API를 사용해 황금 키워드 기반 블로그 제목 초안을 생성합니다.
    할당량 초과 시 자동으로 하위 모델로 다운그레이드합니다.

    모델별 특징:
    - gemini-2.5-pro: 가장 정교한 한국어 문장 생성, 맥락 이해 최상위
    - gemini-2.5-flash: 품질과 속도의 균형, 일반 사용에 충분
    - gemini-2.5-flash-lite: 빠르고 저렴, 간단한 제목 생성에 적합

    Args:
        golden_keywords: 황금 키워드 목록
        api_key: Gemini API 키
        model: 사용할 모델명
        is_cross_mode: 크로스 키워드 모드 여부
        cross_topics: 크로스 모드 시 주제 쌍 목록

    Returns:
        AI가 생성한 블로그 제목 초안 문자열
    """
    if not api_key:
        return "⚠️  Gemini API 키가 설정되지 않아 제목 자동 생성을 건너뜁니다."

    try:
        import google.generativeai as genai
    except ImportError:
        return (
            "⚠️  google-generativeai 패키지가 없습니다.\n"
            "    'pip install google-generativeai' 실행 후 재시도하세요."
        )
    except Exception as e:
        return f"⚠️  google.generativeai 모듈 로딩 오류: {e}"

    # 모델 다운그레이드 순서
    fallback_models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
    if model not in fallback_models:
        fallback_models.insert(0, model)

    for idx, model_name in enumerate(fallback_models):
        try:
            genai.configure(api_key=api_key)

            # 키워드 목록 텍스트 정리 (황금 키워드가 없으면 상위 키워드로 대체 가능)
            keyword_list = "\n".join([
                f"- {kw['keyword']} "
                f"(점수: {kw['score']}, 의도: {kw['search_intent']}, "
                f"블로그경쟁: {kw['blog_competition']})"
                for kw in golden_keywords[:12]
            ])

            # 크로스 모드 전용 프롬프트 추가 지시
            cross_instruction = ""
            if is_cross_mode and cross_topics:
                pairs_text = "\n".join([
                    f"  - '{a}' × '{b}'" for a, b in cross_topics
                ])
                cross_instruction = f"""
[크로스 콘텐츠 특별 지시]
이 분석은 아래 주제들을 연결하는 크로스 콘텐츠를 위한 것입니다:
{pairs_text}

제목 중 최소 2개는 두 주제를 하나의 제목에서 연결하는 형식으로 작성하세요.
예: "계엄 선포 후 다시 보는 영화 1987 | 역사는 반복되는가"
"""

            # Gemini에게 전달할 프롬프트
            # gemini-2.5-pro의 강점인 긴 맥락 이해와 정교한 한국어 문장 생성을 활용
            prompt = f"""당신은 한국 티스토리 블로그 SEO 전문가이자 영화·문화 콘텐츠 에디터입니다.

[블로그 정보]
- 블로그명: MVforrest's blog (forrest125.tistory.com)
- 슬로건: "imagine, save the world"
- 콘텐츠 스타일: 심층 분석형 리뷰 (단순 줄거리 요약이 아닌 맥락·해석·사회적 의미 탐구)
- 주요 독자: 영화·드라마를 깊이 있게 즐기고 싶은 20~40대
- 글쓰기 특징: 개인적 감상 + 학술적 분석 혼합, 시리즈 연재 형식 활용

[상위 키워드 목록 (기회 점수 높은 순)]
{keyword_list}
{cross_instruction}

[블로그 제목 작성 규칙]
1. 제목 길이: 40~65자 (너무 짧으면 정보 부족, 너무 길면 검색 결과에서 잘림)
2. 핵심 키워드는 제목의 앞 20자 이내에 배치 (구글·네이버 검색 결과 표시 기준)
3. 독자의 지적 호기심을 자극하는 표현 사용 ("완벽 정리", "숨겨진 의미", "다시 보는 이유")
4. 숫자나 구체적 정보 포함 시 클릭률 상승 (예: "5가지 이유", "10년 만에 밝혀진")
5. 티스토리 특성상 대괄호 카테고리 표시 활용 가능 (예: [영화 리뷰], [최신 개봉])
6. 각 제목은 서로 다른 상위 키워드를 중심으로 작성 (중복 키워드 사용 최소화)

[출력 형식 — 반드시 아래 형식을 정확히 따르세요]
제목 1: [제목 전문]
→ 핵심 키워드: [사용한 상위 키워드] | 검색 의도: [정보형/탐색형/거래형] | 예상 클릭률: [상/중/하]
→ 선택 이유: [이 제목이 SEO와 독자 유입에 유리한 이유를 2문장으로]

제목 2: ...

(총 5개 제목 작성)

마지막에 [제목 선택 가이드] 섹션을 추가해, 5개 중 어떤 제목을 어떤 상황에 사용하면 좋은지 간략히 설명하세요."""

            # Gemini 모델 초기화 및 호출
            # gemini-2.5-pro는 thinking 기능이 있어 더 정교한 결과를 생성합니다
            model_obj = genai.GenerativeModel(model_name)

            # 생성 설정: 창의성(temperature)과 출력 길이 조절
            # max_output_tokens: gemini-2.5-flash는 thinking 모델로 내부 추론 토큰이 있어
            # 1500으로 두면 응답이 중간에 잘릴 수 있음 → 8192로 충분히 확보
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,      # 0=보수적, 1=창의적 (0.7이 균형점)
                max_output_tokens=8192,  # 최대 출력 토큰 수 (thinking 모델 대응)
            )

            response = model_obj.generate_content(
                prompt,
                generation_config=generation_config,
            )

            # 성공 시 모델 변경 메시지 추가
            success_msg = ""
            if idx > 0:
                success_msg = f"\n✅ Gemini 할당량 부족으로 {model_name} 모델로 변경하여 제목 생성을 완료했습니다.\n"
            return success_msg + response.text

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                # 할당량 초과 오류면 다음 모델로 시도
                if idx < len(fallback_models) - 1:
                    print(f"⚠️  Gemini 할당량 부족 ({model_name}) → {fallback_models[idx+1]} 모델로 변경 시도 중...")
                    continue
                else:
                    return f"⚠️  Gemini API 할당량을 모두 소진했습니다. 다음 날 재시도하거나 유료 플랜을 사용하세요.\n오류: {e}"
            else:
                # 429 외 오류는 즉시 반환
                return f"⚠️  Gemini API 오류: {e}\n모델명 확인: {model_name}"

    return "⚠️  Gemini API 제목 생성을 실패했습니다."


# ──────────────────────────────────────────────────────────────────────────────
# [STEP 5] 결과 저장
# ──────────────────────────────────────────────────────────────────────────────

def save_results(
    results: list[dict],
    ai_titles: str,
    output_dir: str,
    mode_label: str = "일반",
) -> tuple[str, str]:
    """분석 결과를 CSV와 텍스트 리포트로 저장합니다."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"키워드분석_{mode_label}_{timestamp}.csv")
    report_path = os.path.join(output_dir, f"황금키워드_{mode_label}_{timestamp}.txt")

    # CSV 저장
    csv_headers = [
        "키워드", "수요(1단계직접노출)", "블로그경쟁도",
        "VIEW경쟁도", "기회점수", "등급", "검색의도",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "키워드": r["keyword"],
                "수요(1단계직접노출)": "O" if r["has_demand"] else "X",
                "블로그경쟁도": r["blog_competition"],
                "VIEW경쟁도": r["view_competition"],
                "기회점수": r["score"],
                "등급": r["grade"],
                "검색의도": r["search_intent"],
            })

    # 텍스트 리포트 저장
    golden = [r for r in results if r["grade"] == "황금 키워드"]
    promising = [r for r in results if r["grade"] == "유망 키워드"]

    report_lines = [
        "=" * 65,
        f"MVforrest SEO 키워드 분석 리포트 V3  [{mode_label} 모드]",
        f"생성 시각: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}",
        f"사용 모델: {GEMINI_MODEL}",
        "=" * 65,
        "",
        "[분석 요약]",
        f"  총 분석 키워드: {len(results)}개",
        f"  황금 키워드:    {len(golden)}개",
        f"  유망 키워드:    {len(promising)}개",
        "",
        "─" * 65,
        "[황금 키워드 TOP 목록] (점수 높은 순)",
        "─" * 65,
    ]

    for i, kw in enumerate(golden[:15], 1):
        report_lines.append(
            f"  {i:2d}. {kw['keyword']:<28} "
            f"점수:{kw['score']:5.1f}  "
            f"블로그:{kw['blog_competition']:2d}  "
            f"의도:{kw['search_intent']}"
        )

    report_lines += [
        "",
        "─" * 65,
        "[Gemini AI 블로그 제목 초안]",
        "─" * 65,
        ai_titles,
        "",
        "─" * 65,
        "[SEO 적용 체크리스트]",
        "─" * 65,
        "□ 황금 키워드를 제목 앞 20자 이내에 배치",
        "□ 첫 문단(100자 이내)에 핵심 키워드 포함",
        "□ 소제목(H2) 2~3개에 유망 키워드 자연스럽게 삽입",
        "□ 대표 이미지 alt 텍스트에 키워드 포함",
        "□ 태그 5~10개 설정 (황금+유망 키워드 조합)",
        "□ 관련 이전 글에 내부 링크 연결",
        "=" * 65,
    ]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    return csv_path, report_path


def _load_profile(profile_path: str) -> dict:
    if not profile_path:
        return {}
    _, ext = os.path.splitext(profile_path)
    ext = ext.lower().lstrip(".")

    with open(profile_path, "r", encoding="utf-8") as f:
        content = f.read()

    if ext in ("json", ""):
        return json.loads(content)

    if ext in ("yaml", "yml"):
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "YAML profile requires PyYAML. Install with: pip install pyyaml"
            ) from e
        return yaml.safe_load(content) or {}

    raise ValueError(f"Unsupported profile extension: .{ext}")


def _apply_profile_config(cfg: dict) -> None:
    global SEED_KEYWORDS
    global SEARCH_DEPTH
    global MIN_WORDS
    global MAX_WORDS
    global REQUEST_DELAY
    global OUTPUT_DIR
    global CROSS_MODE
    global CROSS_TOPICS
    global GEMINI_MODEL

    if not isinstance(cfg, dict):
        return

    if isinstance(cfg.get("seed_keywords"), list):
        SEED_KEYWORDS = [str(x) for x in cfg["seed_keywords"]]
    if isinstance(cfg.get("search_depth"), int):
        SEARCH_DEPTH = cfg["search_depth"]
    if isinstance(cfg.get("min_words"), int):
        MIN_WORDS = cfg["min_words"]
    if isinstance(cfg.get("max_words"), int):
        MAX_WORDS = cfg["max_words"]
    if isinstance(cfg.get("request_delay"), (int, float)):
        REQUEST_DELAY = float(cfg["request_delay"])
    if isinstance(cfg.get("output_dir"), str) and cfg.get("output_dir"):
        OUTPUT_DIR = cfg["output_dir"]
    if isinstance(cfg.get("cross_mode"), bool):
        CROSS_MODE = cfg["cross_mode"]
    if isinstance(cfg.get("gemini_model"), str) and cfg.get("gemini_model"):
        GEMINI_MODEL = cfg["gemini_model"]

    topics = cfg.get("cross_topics")
    if isinstance(topics, list):
        parsed: list[tuple[str, str]] = []
        for item in topics:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                parsed.append((str(item[0]), str(item[1])))
        if parsed:
            CROSS_TOPICS = parsed


def _parse_cross_topic(value: str) -> tuple[str, str]:
    if "|" not in value:
        raise ValueError("--cross-topic must be in the format 'TOPIC_A|TOPIC_B'")
    a, b = value.split("|", 1)
    a = a.strip()
    b = b.strip()
    if not a or not b:
        raise ValueError("--cross-topic must be in the format 'TOPIC_A|TOPIC_B'")
    return a, b


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--profile", type=str, default="", help="JSON/YAML profile file")
    p.add_argument("--seed", action="append", default=[], help="Seed keyword (repeatable)")
    p.add_argument("--depth", type=int, default=None)
    p.add_argument("--min-words", type=int, default=None)
    p.add_argument("--max-words", type=int, default=None)
    p.add_argument("--request-delay", type=float, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    p.add_argument("--cross-mode", action="store_true")
    p.add_argument("--no-cross-mode", action="store_true")
    p.add_argument(
        "--cross-topic",
        action="append",
        default=[],
        help="Cross topic pair 'A|B' (repeatable)",
    )
    return p


def run_cli(argv: Optional[list[str]] = None) -> None:
    global SEED_KEYWORDS
    global SEARCH_DEPTH
    global MIN_WORDS
    global MAX_WORDS
    global REQUEST_DELAY
    global OUTPUT_DIR
    global CROSS_MODE
    global CROSS_TOPICS

    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.profile:
        cfg = _load_profile(args.profile)
        _apply_profile_config(cfg)

    if args.seed:
        SEED_KEYWORDS = [str(x) for x in args.seed]
    elif args.cross_mode and args.cross_topic:
        # --cross-mode에서 --seed 없이 실행 시 기본 하드코딩 시드가 섞이는 버그 방지
        SEED_KEYWORDS = []
    if args.depth is not None:
        SEARCH_DEPTH = args.depth
    if args.min_words is not None:
        MIN_WORDS = args.min_words
    if args.max_words is not None:
        MAX_WORDS = args.max_words
    if args.request_delay is not None:
        REQUEST_DELAY = float(args.request_delay)
    if args.output_dir is not None and args.output_dir:
        OUTPUT_DIR = args.output_dir

    if args.cross_mode and args.no_cross_mode:
        raise ValueError("Use only one of --cross-mode or --no-cross-mode")
    if args.cross_mode:
        CROSS_MODE = True
    if args.no_cross_mode:
        CROSS_MODE = False

    if args.cross_topic:
        CROSS_TOPICS = [_parse_cross_topic(x) for x in args.cross_topic]

    gemini_key_loaded = bool(GEMINI_API_KEY)
    naver_key_loaded = bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET)
    print(
        "\n[설정 확인] "
        f"GeminiKey={'OK' if gemini_key_loaded else 'MISSING'} | "
        f"NaverOpenAPIKey={'OK' if naver_key_loaded else 'MISSING'} | "
        f"UseNaverOpenAPI={USE_NAVER_OPENAPI} | "
        f"ConfigPath={CONFIG_ORIGIN if CONFIG_ORIGIN else 'NOT_FOUND'}"
    )

    main()


def _print_top_keywords(results: list[dict], top_n: int = 15) -> None:
    if not results:
        return
    print("\n" + "─" * 65)
    print(f"[상위 키워드 TOP {min(top_n, len(results))}] (기회점수 내림차순)")
    print("─" * 65)
    for i, r in enumerate(results[:top_n], 1):
        print(
            f"{i:2d}. {r['keyword']} | 점수:{r['score']:>5} | "
            f"등급:{r['grade']} | 의도:{r['search_intent']} | "
            f"블로그:{r['blog_competition']} | VIEW:{r['view_competition']}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# [MAIN] 전체 실행 흐름
# ──────────────────────────────────────────────────────────────────────────────

def main():
    mode_label = "크로스" if CROSS_MODE else "일반"

    print("\n" + "=" * 65)
    print(f"  MVforrest SEO 키워드 분석기 V3  [{mode_label} 모드]")
    print(f"  AI 모델: {GEMINI_MODEL}")
    print("=" * 65)

    # ── 1단계: 키워드 수집 ──────────────────────────────────
    if CROSS_MODE:
        print("\n[1단계] 크로스 키워드 수집 중...")
        print(f"  분석할 주제 쌍: {CROSS_TOPICS}")
        all_keywords = collect_cross_keywords(CROSS_TOPICS)

        # 일반 시드 키워드도 함께 수집 (있을 경우)
        if SEED_KEYWORDS:
            print("\n  + 일반 시드 키워드도 함께 수집...")
            normal_keywords = collect_keywords_recursive(
                SEED_KEYWORDS, SEARCH_DEPTH, MIN_WORDS, MAX_WORDS
            )
            all_keywords.update(normal_keywords)
    else:
        print("\n[1단계] 구글 자동완성으로 연관 검색어 수집 중...")
        print(f"  시드 키워드: {SEED_KEYWORDS}")
        all_keywords = collect_keywords_recursive(
            SEED_KEYWORDS, SEARCH_DEPTH, MIN_WORDS, MAX_WORDS
        )

    print(f"\n  → 총 {len(all_keywords)}개 키워드 수집 완료")

    # ── 2단계: 경쟁도 측정 ──────────────────────────────────
    print("\n[2단계] 네이버 경쟁도 측정 중...")
    results = []

    for i, (keyword, has_demand) in enumerate(all_keywords.items(), 1):
        print(f"  [{i:3d}/{len(all_keywords)}] {keyword}", end=" ... ", flush=True)

        blog_comp = get_naver_blog_competition(keyword)
        time.sleep(REQUEST_DELAY)
        view_comp = get_naver_view_competition(keyword)
        time.sleep(REQUEST_DELAY)

        score = calculate_opportunity_score(has_demand, blog_comp, view_comp)
        grade = classify_keyword(score, has_demand)
        intent = classify_search_intent(keyword)

        results.append({
            "keyword": keyword,
            "has_demand": has_demand,
            "blog_competition": blog_comp,
            "view_competition": view_comp,
            "score": score,
            "grade": grade,
            "search_intent": intent,
        })

        print(f"점수: {score:5.1f} | {grade}")

    results.sort(key=lambda x: x["score"], reverse=True)

    _print_top_keywords(results, top_n=15)

    # ── 3단계: Gemini AI 제목 생성 ──────────────────────────
    print(f"\n[3단계] Gemini ({GEMINI_MODEL}) 블로그 제목 초안 생성 중...")

    golden_keywords = [r for r in results if r["grade"] == "황금 키워드"]
    title_source_keywords = golden_keywords if golden_keywords else results[:12]
    try:
        ai_titles = generate_blog_titles_with_gemini(
            golden_keywords=title_source_keywords,
            api_key=GEMINI_API_KEY,
            model=GEMINI_MODEL,
            is_cross_mode=CROSS_MODE,
            cross_topics=CROSS_TOPICS if CROSS_MODE else None,
        )
    except Exception as e:
        ai_titles = f"⚠️  Gemini 제목 생성 중 오류: {e}"

    # ── 4단계: 결과 저장 ────────────────────────────────────
    print("\n[4단계] 결과 저장 중...")
    csv_path, report_path = save_results(
        results=results,
        ai_titles=ai_titles,
        output_dir=OUTPUT_DIR,
        mode_label=mode_label,
    )

    # ── 최종 요약 ────────────────────────────────────────────
    golden = [r for r in results if r["grade"] == "황금 키워드"]
    promising = [r for r in results if r["grade"] == "유망 키워드"]

    print("\n" + "=" * 65)
    print("  분석 완료!")
    print("=" * 65)
    print(f"\n  총 분석 키워드: {len(results)}개")
    print(f"  황금 키워드:    {len(golden)}개")
    print(f"  유망 키워드:    {len(promising)}개")

    if golden:
        print("\n  [황금 키워드 TOP 5]")
        for kw in golden[:5]:
            print(f"    ★ {kw['keyword']} (점수: {kw['score']})")

    print(f"\n  📄 CSV:    {csv_path}")
    print(f"  📋 리포트: {report_path}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_cli()
