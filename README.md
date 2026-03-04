# 🎬 Content Trend SEO Toolkit

> **한국 콘텐츠 블로거를 위한 화제성 탐지 + SEO 키워드 분석 자동화 파이프라인**
> 
> Automated pipeline for detecting trending Korean content and optimizing SEO keywords for blog posts.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Pro-orange.svg)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 프로젝트 개요 | Overview

이 툴킷은 **"어떤 콘텐츠를 써야 조회수가 높을까?"** 라는 질문에 데이터로 답합니다.

This toolkit answers the question: **"Which content should I write to maximize views?"** — using real data, not guesswork.

### 핵심 기능 | Core Features

| 기능 | 설명 |
|---|---|
| **SEO 키워드 분석** | 구글 자동완성 + 네이버 경쟁도 측정 → 기회 점수 산출 |
| **화제성 탐지** | 구글 트렌드(KR) + 네이버 데이터랩 + 뉴스 RSS 교차 분석 |
| **AI 제목 생성** | Gemini 2.5 Pro가 분석 결과 기반으로 블로그 제목 초안 자동 생성 |
| **통합 대시보드** | 분석 결과를 인터랙티브 웹 UI로 시각화 (팀 공유 가능) |

---

## 🏗️ 시스템 아키텍처 | Architecture

```
[데이터 수집 레이어]
  구글 자동완성 API ──┐
  네이버 블로그 검색 ──┤
  구글 트렌드 (KR) ───┤──→ [스코어링 엔진] ──→ [Gemini AI] ──→ [CSV + 리포트]
  Google News RSS ────┘         │
                                ↓
                        [웹 대시보드 시각화]
                        seokeyword-qjyzzhbx.manus.space
```

---

## 📁 파일 구조 | File Structure

```
content-trend-seo-toolkit/
├── README.md
├── requirements.txt
├── mvforrest_seo_v3.py        # SEO 키워드 분석기 (메인)
├── results/
│   └── sample_output.csv      # 샘플 분석 결과
└── docs/
    └── usage_guide.md         # 상세 사용 가이드
```

---

## 🚀 빠른 시작 | Quick Start

### 1. 설치

```bash
git clone https://github.com/kimble125/content-trend-seo-toolkit.git
cd content-trend-seo-toolkit
pip install -r requirements.txt
```

### 2. API 키 설정

```python
# mvforrest_seo_v3.py 상단 CONFIG 수정
GEMINI_API_KEY = "your-api-key-here"  # https://aistudio.google.com
```

### 3. 실행

```bash
python mvforrest_seo_v3.py
```

### 4. 결과 확인

`results/` 폴더에 CSV 파일과 텍스트 리포트가 자동 생성됩니다.

---

## 📊 분석 결과 예시 | Sample Output

| 키워드 | 수요 | 경쟁도 | 기회 점수 | 등급 |
|---|---|---|---|---|
| 베를린 휴민트 사건 정리 | O | 3개 | 25.0 | 🔥 대박 |
| 휴민트 루민트 차이점 | O | 1개 | 50.0 | 🔥 대박 |
| 영화 휴민트 줄거리 | O | 12개 | 7.7 | 👀 중박 |
| 휴민트 넷플릭스 | O | 45개 | 2.2 | ⚠️ 경쟁 심함 |

---

## 🔑 기회 점수 공식 | Opportunity Score Formula

```
Opportunity Score = 100 ÷ (네이버 블로그 경쟁 포스트 수 + 1)

해석:
  80~100점 → 🔥 대박 (수요 있음 + 경쟁 거의 없음)
  50~79점  → 👀 중박 (공략 가능)
  20~49점  → ⚠️ 신중 (경쟁 있음)
  0~19점   → 💤 패스 (레드오션)
```

---

## 🌐 웹 대시보드 | Web Dashboard

분석 결과를 팀과 공유할 수 있는 인터랙티브 대시보드:

**→ [Live Demo](https://seokeyword-qjyzzhbx.manus.space)**

McKinsey Insights 스타일의 전략 브리핑 문서 형태로 구현되었습니다.

---

## 🛠️ 기술 스택 | Tech Stack

- **Language:** Python 3.8+
- **AI:** Google Gemini 2.5 Pro API
- **Data Sources:** Google Suggest API, Naver Blog Search, Google Trends, Google News RSS
- **Web Dashboard:** React 19 + Tailwind CSS 4 + Recharts
- **Deployment:** Manus (manus.space)

---

## 📈 활용 사례 | Use Cases

이 툴킷은 다음 블로그의 SEO 전략 수립에 실제로 활용되고 있습니다:

- **MVforrest 블로그:** [forrest125.tistory.com](https://forrest125.tistory.com) — 영화·드라마 심층 리뷰 (41편+)

---

## 🗺️ 로드맵 | Roadmap

- [x] V1: 구글 자동완성 기반 키워드 수집
- [x] V2: 네이버 경쟁도 측정 + 기회 점수 산출
- [x] V3: Gemini AI 연동 + 크로스 키워드 모드
- [ ] V4: 화제성 탐지 모듈 (구글 트렌드 KR + 네이버 데이터랩)
- [ ] V5: SQLite 적재 + SQL 분석 지원
- [ ] V6: 커뮤니티 버전 (오픈소스 AI 지원)

---

## 📄 라이선스 | License

MIT License — 자유롭게 사용, 수정, 배포 가능합니다.

---

*Made with ❤️ by [kimble125](https://github.com/kimble125) | [Blog](https://forrest125.tistory.com)*
