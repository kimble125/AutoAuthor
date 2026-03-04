"""
content_planner.py — AI 기획안 자동 생성 모듈 (V5)
=================================================

[목적]
사용자가 작품명을 입력하면:
  1) 해당 작품의 화제성 키워드를 자동 수집
  2) 키워드별 포화도(경쟁도)를 측정
  3) 황금 키워드를 선별
  4) Gemini 2.5 Pro가 기획안 후보 3종을 자동 생성
     (제목, 소제목 5개, 간략 소개, 우선순위 포함)

[실행 방법]
  pip install requests beautifulsoup4 google-generativeai
  python content_planner.py

[AI 모델 안내]
  현재: Gemini 2.5 Pro (Google AI Studio 무료 API 키)
  서비스 출시 시 대체 가능한 오픈소스 AI:
    - EXAONE 3.5 (LG AI, 한국어 특화, Apache 2.0 라이선스, 완전 무료)
    - Qwen2.5-72B (Alibaba, 한국어 우수, vLLM 셀프 호스팅)
    - Groq + llama-3.3-70b (무료 할당량 내 사용 가능)
    - Ollama 로컬 실행 (인터넷 불필요, 개인정보 보호)
"""

import requests
import re
import time
import json
import csv
import os
from datetime import datetime
from bs4 import BeautifulSoup

# ╔══════════════════════════════════════════════════════════════╗
# ║                    🔧 CONFIG (설정 구역)                      ║
# ║  이 부분만 수정하면 어떤 작품에도 바로 적용할 수 있습니다.         ║
# ╚══════════════════════════════════════════════════════════════╝

CONFIG = {
    # ── 분석 대상 작품 ──────────────────────────────────────
    # 작품명을 입력하세요. 실행 시 input()으로도 입력 가능합니다.
    "CONTENT_TITLE": "",  # 비워두면 실행 시 직접 입력

    # ── 작품 유형 (영화/드라마/애니메이션/쇼/웹툰) ──────────
    "CONTENT_TYPE": "",   # 비워두면 실행 시 직접 입력

    # ── Gemini API 설정 ─────────────────────────────────────
    # API 키 발급: https://aistudio.google.com → Get API key
    "GEMINI_API_KEY": "",  # 비워두면 AI 기획안 생성 단계를 건너뜁니다

    # 사용할 모델 (한국어 품질 순):
    #   "gemini-2.5-pro"        ← 최고 품질 (기본값)
    #   "gemini-2.5-flash"      ← 빠른 속도
    #   "gemini-2.5-flash-lite" ← 대량 처리용
    "GEMINI_MODEL": "gemini-2.5-pro",

    # ── 키워드 수집 설정 ────────────────────────────────────
    # 시드 키워드 접미사 (작품명 뒤에 자동으로 붙는 단어들)
    "SEED_SUFFIXES": [
        "",           # 작품명 단독
        " 리뷰",
        " 줄거리",
        " 결말",
        " 출연진",
        " 평점",
        " 해석",
        " 실화",
        " 원작",
        " 촬영지",
        " OST",
        " 시즌2",
        " 논란",
        " 명대사",
        " 비하인드",
    ],

    # 요청 간격 (초). 너무 빠르면 차단될 수 있습니다.
    "SLEEP_TIME": 0.5,

    # 결과 저장 디렉토리
    "OUTPUT_DIR": "results",

    # ── 기획안 생성 설정 ────────────────────────────────────
    # 블로그 플랫폼 (기획안 톤 조절용)
    "BLOG_PLATFORM": "티스토리",

    # 블로그 URL (기획안에 참조용으로 포함)
    "BLOG_URL": "https://forrest125.tistory.com",

    # 기획안 후보 수
    "NUM_PROPOSALS": 3,
}


# ╔══════════════════════════════════════════════════════════════╗
# ║              📡 STEP 1: 화제성 키워드 수집                     ║
# ╚══════════════════════════════════════════════════════════════╝

def get_google_suggestions(query: str) -> list[str]:
    """
    구글 자동완성 API에서 연관 검색어를 가져옵니다.
    자동완성에 등장한다 = 최소한의 검색 수요가 존재한다는 신호입니다.
    """
    url = "http://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",   # JSON 형식으로 응답받기 위한 설정
        "q": query,
        "hl": "ko",            # 한국어 결과
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data[1] if len(data) > 1 else []
    except Exception as e:
        print(f"  ⚠️ 구글 자동완성 오류: {e}")
    return []


def collect_keywords(title: str, content_type: str) -> list[str]:
    """
    작품명 + 접미사 조합으로 구글 자동완성 키워드를 대량 수집합니다.
    """
    print(f"\n📡 STEP 1: '{title}' 관련 키워드 수집 중...")
    all_keywords = set()

    # 기본 시드: 작품명 + 접미사
    seeds = [f"{title}{suffix}" for suffix in CONFIG["SEED_SUFFIXES"]]

    # 콘텐츠 유형별 추가 시드
    type_prefixes = {
        "영화": ["영화 ", ""],
        "드라마": ["드라마 ", ""],
        "애니메이션": ["애니 ", "애니메이션 ", ""],
        "쇼": ["", "예능 "],
        "웹툰": ["웹툰 ", ""],
    }
    prefixes = type_prefixes.get(content_type, [""])
    for prefix in prefixes:
        for suffix in CONFIG["SEED_SUFFIXES"][:8]:  # 주요 접미사만
            seeds.append(f"{prefix}{title}{suffix}")

    # 중복 제거
    seeds = list(set(seeds))

    for seed in seeds:
        suggestions = get_google_suggestions(seed)
        for kw in suggestions:
            # 작품명이 포함된 키워드만 수집 (무관한 결과 필터링)
            if title.replace(" ", "") in kw.replace(" ", ""):
                all_keywords.add(kw.strip())
        time.sleep(CONFIG["SLEEP_TIME"])

    # 2단계 확장: 수집된 키워드 중 상위 5개로 추가 탐색
    top_keywords = list(all_keywords)[:5]
    for kw in top_keywords:
        suggestions = get_google_suggestions(kw)
        for s in suggestions:
            if title.replace(" ", "") in s.replace(" ", ""):
                all_keywords.add(s.strip())
        time.sleep(CONFIG["SLEEP_TIME"])

    result = sorted(all_keywords)
    print(f"  ✅ 총 {len(result)}개 키워드 수집 완료")
    return result


# ╔══════════════════════════════════════════════════════════════╗
# ║              📊 STEP 2: 포화도(경쟁도) 측정                    ║
# ╚══════════════════════════════════════════════════════════════╝

def measure_saturation(keyword: str) -> int:
    """
    네이버 블로그 검색 결과에서 1페이지 포스트 수를 세어 포화도를 측정합니다.
    포스트 수가 적을수록 블루오션(경쟁 낮음)입니다.
    """
    url = "https://search.naver.com/search.naver"
    params = {"where": "blog", "query": keyword}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # 블로그 포스트 제목 요소 카운팅
            posts = soup.select("a.title_link") or soup.select(".title_area a")
            return len(posts)
    except Exception as e:
        print(f"  ⚠️ 포화도 측정 오류 ({keyword}): {e}")
    return -1  # 측정 실패


def classify_saturation(post_count: int) -> str:
    """포스트 수를 기반으로 포화도 등급을 분류합니다."""
    if post_count <= 5:
        return "블루"    # 🫧 블루 오션 (0~5개)
    elif post_count <= 20:
        return "퍼플"    # ⛵ 퍼플 오션 (6~20개)
    elif post_count <= 100:
        return "레드"    # 🦈 레드 오션 (21~100개)
    else:
        return "블랙"    # ☠️ 블랙 오션 (100개 초과)


def classify_search_intent(keyword: str) -> str:
    """키워드의 검색 의도를 자동 분류합니다."""
    info_patterns = ["정리", "해석", "분석", "의미", "비교", "차이", "설명", "이유", "배경", "실화", "원작"]
    compare_patterns = ["vs", "차이점", "비교", "어떤", "뭐가"]
    transaction_patterns = ["다운", "무료", "보기", "스트리밍", "넷플릭스", "왓챠", "쿠팡"]

    for p in compare_patterns:
        if p in keyword:
            return "비교형"
    for p in info_patterns:
        if p in keyword:
            return "정보형"
    for p in transaction_patterns:
        if p in keyword:
            return "거래형"
    return "탐색형"


def analyze_keywords(keywords: list[str]) -> list[dict]:
    """
    수집된 키워드 전체에 대해 포화도를 측정하고 등급을 부여합니다.
    """
    print(f"\n📊 STEP 2: {len(keywords)}개 키워드 포화도 측정 중...")
    results = []

    for i, kw in enumerate(keywords):
        post_count = measure_saturation(kw)
        saturation = classify_saturation(post_count) if post_count >= 0 else "측정실패"
        intent = classify_search_intent(kw)

        # 기회 점수 계산: 100 / (포스트 수 + 1)
        score = 100 / (post_count + 1) if post_count >= 0 else 0

        results.append({
            "keyword": kw,
            "competition": post_count,
            "saturation": saturation,
            "score": round(score, 1),
            "intent": intent,
            "is_golden": saturation in ["블루", "퍼플"] and post_count >= 0,
        })

        # 진행 상황 표시
        if (i + 1) % 5 == 0 or i == len(keywords) - 1:
            print(f"  [{i+1}/{len(keywords)}] 측정 완료")

        time.sleep(CONFIG["SLEEP_TIME"])

    # 기회 점수 내림차순 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    golden = [r for r in results if r["is_golden"]]
    print(f"  ✅ 포화도 측정 완료 — 황금 키워드 {len(golden)}개 발견")
    return results


# ╔══════════════════════════════════════════════════════════════╗
# ║           🤖 STEP 3: AI 기획안 자동 생성 (Gemini)              ║
# ╚══════════════════════════════════════════════════════════════╝

def generate_content_plans(
    title: str,
    content_type: str,
    keyword_results: list[dict],
) -> str:
    """
    황금 키워드를 Gemini에 전달하여 기획안 후보 3종을 자동 생성합니다.

    각 기획안 구조:
      - 제목 (SEO 최적화)
      - 소제목 5개 (들어가며 / 본문1 / 본문2 / 본문3 / 마치며)
      - 간략한 소개 (150자 내외)
      - 타깃 키워드 목록
      - 예상 화제성 × 포화도 등급
    """
    api_key = CONFIG["GEMINI_API_KEY"]
    if not api_key:
        print("\n⚠️ GEMINI_API_KEY가 설정되지 않아 AI 기획안 생성을 건너뜁니다.")
        print("  → CONFIG['GEMINI_API_KEY']에 API 키를 입력하세요.")
        print("  → 발급: https://aistudio.google.com → Get API key")
        return ""

    print(f"\n🤖 STEP 3: Gemini {CONFIG['GEMINI_MODEL']}로 기획안 생성 중...")

    # 황금 키워드 (블루/퍼플 오션) 추출
    golden = [r for r in keyword_results if r["is_golden"]][:15]
    other = [r for r in keyword_results if not r["is_golden"]][:10]

    golden_text = "\n".join([
        f"  - {r['keyword']} (포화도: {r['saturation']}, 점수: {r['score']}, 의도: {r['intent']})"
        for r in golden
    ])
    other_text = "\n".join([
        f"  - {r['keyword']} (포화도: {r['saturation']}, 점수: {r['score']})"
        for r in other
    ])

    # ── Gemini 프롬프트 ──────────────────────────────────────
    prompt = f"""당신은 한국 콘텐츠 블로그 SEO 전문가입니다.

아래 데이터를 분석하여, {CONFIG['BLOG_PLATFORM']} 블로그에 작성할 '{title}' ({content_type}) 리뷰 기획안 후보 {CONFIG['NUM_PROPOSALS']}개를 작성해 주세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 키워드 분석 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[황금 키워드 — 블루/퍼플 오션 (최우선 공략)]
{golden_text if golden_text else "  (없음 — 전체 키워드에서 선별해 주세요)"}

[기타 키워드 — 레드/블랙 오션 (참고용)]
{other_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 기획안 작성 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 각 기획안은 반드시 아래 구조를 따르세요:
   - 제목: SEO 최적화 (황금 키워드를 제목 앞부분에 배치)
   - 소제목 5개:
     H2: 들어가며 (도입부 — 독자의 관심을 끄는 질문이나 상황 제시)
     H2: 본문 1 (핵심 분석 — 작품의 가장 중요한 포인트)
     H2: 본문 2 (심층 해석 — 숨겨진 의미, 비교, 맥락)
     H2: 본문 3 (부가 정보 — 비하인드, 촬영지, OST 등)
     H2: 마치며 (총평 및 추천 — 별점이나 한줄평 포함)
   - 간략한 소개: 150자 내외 (메타 디스크립션용)
   - 타깃 키워드: 3~5개
   - 예상 등급: 화제성(천상계/우상향/잔잔/냉동) × 포화도(블루/퍼플/레드/블랙)

2. 기획안 {CONFIG['NUM_PROPOSALS']}개의 차별화 전략:
   - 기획안 1 (최우선): 가장 높은 기회 점수 키워드 조합. 정보형 의도 중심.
   - 기획안 2 (추천): 차별화된 각도 (비교형, 크로스 키워드 활용).
   - 기획안 3 (대안): 롱테일 전략 (니치 키워드, 매니아 타깃).

3. 제목 작성 공식:
   [핵심 키워드] + [작품명] + [부제: 독자 호기심 자극]
   예: "영화 휴민트 줄거리 요약 + 결말 해석 | 베를린 휴민트 사건의 실체"

4. 톤: 전문적이면서도 친근한 블로그 톤. 과도한 감탄사 자제.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위 규칙에 따라 기획안 {CONFIG['NUM_PROPOSALS']}개를 작성해 주세요.
각 기획안은 [기획안 1], [기획안 2], [기획안 3]으로 구분해 주세요.
"""

    # ── Gemini API 호출 ──────────────────────────────────────
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(CONFIG["GEMINI_MODEL"])
        response = model.generate_content(prompt)
        result = response.text
        print(f"  ✅ 기획안 {CONFIG['NUM_PROPOSALS']}종 생성 완료")
        return result
    except ImportError:
        print("  ⚠️ google-generativeai 패키지가 없습니다.")
        print("  → pip install google-generativeai")
        return ""
    except Exception as e:
        print(f"  ⚠️ Gemini API 오류: {e}")
        # REST API 폴백
        print("  → REST API로 재시도합니다...")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{CONFIG['GEMINI_MODEL']}:generateContent"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 4096},
            }
            resp = requests.post(
                f"{url}?key={api_key}",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  ✅ 기획안 {CONFIG['NUM_PROPOSALS']}종 생성 완료 (REST API)")
                return result
            else:
                print(f"  ⚠️ REST API 오류: {resp.status_code} — {resp.text[:200]}")
                return ""
        except Exception as e2:
            print(f"  ⚠️ REST API 폴백도 실패: {e2}")
            return ""


# ╔══════════════════════════════════════════════════════════════╗
# ║              💾 STEP 4: 결과 저장                              ║
# ╚══════════════════════════════════════════════════════════════╝

def save_results(
    title: str,
    content_type: str,
    keyword_results: list[dict],
    content_plans: str,
):
    """분석 결과를 CSV + 텍스트 리포트로 저장합니다."""
    os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r'[^\w가-힣]', '_', title)

    # ── CSV 저장 ─────────────────────────────────────────────
    csv_path = os.path.join(CONFIG["OUTPUT_DIR"], f"키워드분석_{safe_title}_{timestamp}.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "keyword", "competition", "saturation", "score", "intent", "is_golden"
        ])
        writer.writeheader()
        for r in keyword_results:
            writer.writerow(r)
    print(f"\n💾 CSV 저장: {csv_path}")

    # ── 텍스트 리포트 저장 ───────────────────────────────────
    report_path = os.path.join(CONFIG["OUTPUT_DIR"], f"기획안_{safe_title}_{timestamp}.txt")
    golden = [r for r in keyword_results if r["is_golden"]]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"  AutoAuthor 기획안 리포트\n")
        f.write(f"  작품: {title} ({content_type})\n")
        f.write(f"  생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"📊 분석 요약\n")
        f.write(f"  총 수집 키워드: {len(keyword_results)}개\n")
        f.write(f"  황금 키워드 (블루/퍼플): {len(golden)}개\n")
        f.write(f"  레드/블랙 오션: {len(keyword_results) - len(golden)}개\n\n")

        f.write("─" * 60 + "\n")
        f.write("🏆 황금 키워드 TOP 10\n")
        f.write("─" * 60 + "\n")
        for i, r in enumerate(golden[:10], 1):
            icon = {"블루": "🫧", "퍼플": "⛵"}.get(r["saturation"], "")
            f.write(f"  {i:2d}. {icon} {r['keyword']}\n")
            f.write(f"      포화도: {r['saturation']} | 점수: {r['score']} | 의도: {r['intent']}\n")
        f.write("\n")

        if content_plans:
            f.write("─" * 60 + "\n")
            f.write("🤖 AI 기획안 후보\n")
            f.write("─" * 60 + "\n\n")
            f.write(content_plans)
            f.write("\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("  Generated by AutoAuthor Content Planner v5.0\n")
        f.write(f"  Blog: {CONFIG['BLOG_URL']}\n")
        f.write("=" * 60 + "\n")

    print(f"📝 리포트 저장: {report_path}")
    return csv_path, report_path


# ╔══════════════════════════════════════════════════════════════╗
# ║                    🚀 메인 실행                                ║
# ╚══════════════════════════════════════════════════════════════╝

def main():
    print("=" * 60)
    print("  🎬 AutoAuthor Content Planner v5.0")
    print("  화제성 키워드 수집 → 포화도 측정 → AI 기획안 자동 생성")
    print("=" * 60)

    # 작품 정보 입력
    title = CONFIG["CONTENT_TITLE"]
    if not title:
        title = input("\n📌 분석할 작품명을 입력하세요: ").strip()
        if not title:
            print("⚠️ 작품명이 입력되지 않았습니다.")
            return

    content_type = CONFIG["CONTENT_TYPE"]
    if not content_type:
        print("\n📌 콘텐츠 유형을 선택하세요:")
        print("  1) 영화  2) 드라마  3) 애니메이션  4) 쇼/예능  5) 웹툰")
        type_map = {"1": "영화", "2": "드라마", "3": "애니메이션", "4": "쇼", "5": "웹툰"}
        choice = input("  번호 입력 (기본값: 1): ").strip() or "1"
        content_type = type_map.get(choice, "영화")

    print(f"\n🎯 분석 대상: {title} ({content_type})")
    print(f"🤖 AI 모델: {CONFIG['GEMINI_MODEL']}")
    print(f"📂 결과 저장: {CONFIG['OUTPUT_DIR']}/")

    # STEP 1: 키워드 수집
    keywords = collect_keywords(title, content_type)
    if not keywords:
        print("⚠️ 수집된 키워드가 없습니다. 작품명을 확인해 주세요.")
        return

    # STEP 2: 포화도 측정
    keyword_results = analyze_keywords(keywords)

    # STEP 3: AI 기획안 생성
    content_plans = generate_content_plans(title, content_type, keyword_results)

    # STEP 4: 결과 저장
    csv_path, report_path = save_results(title, content_type, keyword_results, content_plans)

    # 최종 요약
    golden = [r for r in keyword_results if r["is_golden"]]
    print("\n" + "=" * 60)
    print("  ✅ 분석 완료!")
    print(f"  📊 총 {len(keyword_results)}개 키워드 분석")
    print(f"  🏆 황금 키워드 {len(golden)}개 발견")
    if content_plans:
        print(f"  🤖 기획안 {CONFIG['NUM_PROPOSALS']}종 생성 완료")
    print(f"  📂 결과 파일: {csv_path}")
    print(f"  📝 리포트 파일: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
