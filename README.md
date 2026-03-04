# Content Trend SEO Toolkit — AutoAuthor v4.0

> **한국 콘텐츠 블로거를 위한 화제성 탐지 + SEO 키워드 분석 + AI 기획안 자동 생성 파이프라인**
> 
> Automated pipeline for detecting trending Korean content, optimizing SEO keywords, and generating blog content plans with AI.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Pro-orange.svg)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 프로젝트 개요 | Overview

이 툴킷은 **"어떤 콘텐츠를 써야 조회수가 높을까?"** 라는 질문에 데이터로 답합니다.

This toolkit answers the question: **"Which content should I write to maximize views?"** — using real data, not guesswork.

### 핵심 기능 | Core Features

| 기능 | 설명 |
|---|---|
| **SEO 키워드 분석** | 구글 자동완성 + 네이버 경쟁도 측정 → 기회 점수 산출 |
| **화제성 4단계 등급** | 👑 천상계 / 📈 우상향 / 💬 잔잔한 수요 / 🧊 냉동창고 |
| **포화도 4단계 등급** | 🫧 블루 오션 / ⛵ 퍼플 오션 / 🦈 레드 오션 / ☠️ 블랙 오션 |
| **AI 기획안 생성** | Gemini 2.5 Pro가 황금 키워드 기반으로 블로그 기획안 3종 자동 생성 |
| **통합 대시보드** | 분석 결과를 인터랙티브 웹 UI로 시각화 (CSV 업로드 지원) |

---

## 시스템 아키텍처 | Architecture

```
[데이터 수집 레이어]
  구글 자동완성 API ──┐
  네이버 블로그 검색 ──┤
  구글 트렌드 (KR) ───┤──→ [스코어링 엔진] ──→ [Gemini 2.5 Pro] ──→ [기획안 3종]
  Google News RSS ────┘    화제성 × 포화도           │
                           4단계 매트릭스             ↓
                                              [CSV + 리포트]
                                                    │
                                                    ↓
                                          [웹 대시보드 시각화]
```

---

## 파일 구조 | File Structure

```
content-trend-seo-toolkit/
├── README.md
├── requirements.txt
├── mvforrest_seo_v3.py        # SEO 키워드 분석기 (V3 — Gemini 연동)
├── content_planner.py         # AI 기획안 자동 생성기 (V5 — 풀 파이프라인)
├── results/
│   └── sample_output.csv      # 샘플 분석 결과
└── docs/
    ├── usage_guide.md         # 상세 사용 가이드
    └── 콘텐츠_성장_전략_가이드.md  # 채널 통합 성장 전략 (크로스 키워드 포함)
```

---

## 빠른 시작 | Quick Start

### 1. 설치

```bash
git clone https://github.com/kimble125/content-trend-seo-toolkit.git
cd content-trend-seo-toolkit
pip install -r requirements.txt
```

### 2. API 키 설정

```python
# content_planner.py 또는 mvforrest_seo_v3.py 상단 CONFIG 수정
GEMINI_API_KEY = "your-api-key-here"  # https://aistudio.google.com 에서 무료 발급
```

### 3. 실행

```bash
# 방법 A: 키워드 분석만 (빠른 실행)
python mvforrest_seo_v3.py

# 방법 B: 키워드 분석 + AI 기획안 자동 생성 (풀 파이프라인)
python content_planner.py
```

### 4. 결과 확인

`results/` 폴더에 CSV 파일과 텍스트 리포트가 자동 생성됩니다.

---

## AutoAuthor 등급 시스템 | Grading System

### 화제성 등급 (Trend Grade)

| 등급 | 점수 범위 | 설명 |
|---|---|---|
| 👑 천상계 도달 | 75~100 | 검색량 폭발. 시장을 지배한 넘사벽 1위 |
| 📈 우상향 탑승 | 45~74 | 입소문을 타기 시작해 검색량이 가파르게 상승 중 |
| 💬 잔잔한 수요 | 15~44 | 매니아층이 꾸준히 검색하는 안정적 상태 |
| 🧊 냉동 창고 | 0~14 | 대중의 관심이 식어 검색량이 거의 없음 |

### 포화도 등급 (Saturation Grade)

| 등급 | 포스트 수 | 설명 |
|---|---|---|
| 🫧 블루 오션 | 0~5개 | 경쟁 없음. 상위 노출 확정 |
| ⛵ 퍼플 오션 | 6~20개 | 독창적 기획으로 충분히 뚫을 수 있는 기회 |
| 🦈 레드 오션 | 21~100개 | 포화 상태. 높은 체급 필요 |
| ☠️ 블랙 오션 | 100개 초과 | 대형 매체가 장악. 진입 비추 |

### 전략 매트릭스 (화제성 × 포화도)

| | 🫧 블루 | ⛵ 퍼플 | 🦈 레드 | ☠️ 블랙 |
|---|---|---|---|---|
| 👑 천상계 | **최우선 공략** | 즉시 착수 | 차별화 필수 | 세부 우회 |
| 📈 우상향 | 지금 당장 | **탑승 적기** | 신중하게 | 포기 권장 |
| 💬 잔잔 | 롱테일 공략 | 차별화 필요 | 비추 | 절대 비추 |
| 🧊 냉동 | 니치 전략 | 비추 | 절대 비추 | 절대 비추 |

---

## AI 기획안 자동 생성 | Content Planner

`content_planner.py`는 작품명을 입력하면 다음을 자동으로 수행합니다:

1. **키워드 수집** — 구글 자동완성 API로 연관 키워드 대량 수집
2. **포화도 측정** — 네이버 블로그 포스트 수 → 4단계 등급 분류
3. **황금 키워드 선별** — 블루/퍼플 오션 키워드만 필터링
4. **AI 기획안 생성** — Gemini 2.5 Pro가 기획안 후보 3종 자동 작성

### 기획안 출력 구조

```
기획안 #1 (우선순위: ★★★ 최우선 공략)
──────────────────────────────
제목: [SEO 최적화 제목 — 황금 키워드 앞 20자 이내 배치]

H2-1: 들어가며 — 독자의 관심을 끄는 질문이나 상황 제시
H2-2: 본문 1 — 핵심 분석
H2-3: 본문 2 — 심층 해석
H2-4: 본문 3 — 부가 정보
H2-5: 마치며 — 총평 및 추천

간략 소개: [150자 내외 메타 디스크립션]
타깃 키워드: [키워드1, 키워드2, ...]
```

---

## 분석 결과 예시 | Sample Output

| 키워드 | 수요 | 경쟁도 | 점수 | 화제성 | 포화도 |
|---|---|---|---|---|---|
| 휴민트 감독판 | O | 1개 | 50.0 | 💬 잔잔 | 🫧 블루 |
| 휴민트 루민트 차이점 | O | 2개 | 33.3 | 📈 우상향 | 🫧 블루 |
| 베를린 휴민트 사건 정리 | O | 3개 | 25.0 | 💬 잔잔 | 🫧 블루 |
| 휴민트 줄거리 | O | 45개 | 2.2 | 👑 천상계 | 🦈 레드 |

---

## 웹 대시보드 | Web Dashboard

분석 결과를 팀과 공유할 수 있는 인터랙티브 대시보드:

**→ [Live Demo](https://seokeyword-qjyzzhbx.manus.space)**

주요 기능:
- CSV 파일 업로드 → 키워드 테이블 실시간 갱신
- 화제성 × 포화도 전략 매트릭스 시각화
- 트렌드 미니 차트 (7일간 검색량 패턴)
- AI 기획안 3종 예시 카드
- 파이프라인 설계 문서 내장

---

## AI 모델 옵션 | AI Model Options

| 용도 | 모델 | 비고 |
|---|---|---|
| **개인 사용 (기본)** | Gemini 2.5 Pro | Google AI Studio 무료 API, 한국어 최고 품질 |
| 빠른 초안 | Gemini 2.5 Flash | 속도 우선 시 |
| **서비스 출시 (오픈소스)** | EXAONE 3.5 (LG AI) | 한국어 특화, Apache 2.0, 완전 무료 |
| 대안 | Qwen2.5-72B | 한국어 우수, vLLM 셀프 호스팅 |
| 대안 | Groq + llama-3.3-70b | 무료 할당량 내 사용 가능 |
| 로컬 실행 | Ollama | 인터넷 불필요, 개인정보 보호 |

---

## 기술 스택 | Tech Stack

- **Language:** Python 3.8+
- **AI:** Google Gemini 2.5 Pro API (교체 가능)
- **Data Sources:** Google Suggest API, Naver Blog Search, Google Trends (KR), Google News RSS
- **Web Dashboard:** React 19 + Tailwind CSS 4 + Recharts + shadcn/ui
- **Deployment:** Manus (manus.space)

---

## 활용 사례 | Use Cases

이 툴킷은 다음 블로그의 SEO 전략 수립에 실제로 활용되고 있습니다:

- **MVforrest 블로그:** [forrest125.tistory.com](https://forrest125.tistory.com) — 영화·드라마 심층 리뷰 (41편+)

---

## 로드맵 | Roadmap

- [x] V1: 구글 자동완성 기반 키워드 수집
- [x] V2: 네이버 경쟁도 측정 + 기회 점수 산출
- [x] V3: Gemini AI 연동 + 크로스 키워드 모드
- [x] V4: AutoAuthor 화제성 × 포화도 4단계 등급 시스템
- [x] V5: AI 기획안 자동 생성 (content_planner.py)
- [ ] V6: 화제성 탐지 모듈 (구글 트렌드 KR + 네이버 데이터랩)
- [ ] V7: SQLite 적재 + SQL 분석 지원
- [ ] V8: 커뮤니티 버전 (오픈소스 AI 지원)

---

## 라이선스 | License

MIT License — 자유롭게 사용, 수정, 배포 가능합니다.

---

*Made with data-driven passion by [kimble125](https://github.com/kimble125) | [Blog](https://forrest125.tistory.com)*
