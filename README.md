# AutoAuthor

> **한국 콘텐츠 블로거를 위한 화제성 탐지 + SEO 키워드 분석 + AI 기획안 자동 생성 파이프라인**
> 
> AI-powered content planning & SEO keyword analyzer for Korean bloggers — from trend detection to publish-ready content plans.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Pro-orange.svg)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Demo-Live%20Dashboard-brightgreen.svg)](https://seokeyword-qjyzzhbx.manus.space)

---

## 프로젝트 개요 | Overview

**"어떤 키워드로 어디에 써야 조회수가 터질까?"** — AutoAuthor는 이 질문에 가장 정밀한 데이터로 답합니다.

단순한 '추측'이 아닙니다. **네이버 검색광고 API**의 실제 월간 검색량과 **YouTube Data API**의 상위 영상 평균 조회수를 기반으로, 플랫폼별 **포화율(Saturation Rate)**을 계산합니다. 이를 통해 네이버 블로그, 유튜브, 티스토리 등 각 플랫폼에서 지금 당장 진입해야 할 **'황금 키워드'**를 기반으로 발굴합니다.

### 핵심 기능 | Core Features

| 기능 | 설명 |
|---|---|
| 멀티 플랫폼 분석 | 네이버(블로그/검색), 유튜브(영상수/조회수), 카카오(다음 검색) 교차 평가 |
| 고정밀 스코어링 | 프록시가 아닌 **실제 월간 검색량** 기반 포화율 알고리즘 적용 |
| 플랫폼별 추천등급 | 같은 키워드라도 플랫폼별 경쟁 우위가 다름을 ★★★ 등급으로 표시 |
| AI 기획안 자동 생성 | Gemini 2.5 Flash가 수집된 황금 키워드 기반 맞춤형 콘텐츠 기획안 작성 |
| 통합 파이프라인 | 발굴(Detection) → 평가(Scoring) → 기획(Planning)의 완전 자동화 |

---

## 시스템 아키텍처 | Architecture

```
[데이터 발굴 레이어]
  TMDB (화제작 정보) ──┐
  Google News RSS   ──┤
  WatchaPedia       ──┤──→ [발굴된 시드 키워드]
  Google Suggest    ──┘            │
                                   ↓
[멀티 플랫폼 평가 레이어]  ← [시장 규모 및 공급 측정]
  Naver Ad API (검색량) ──┐        │
  Naver Blog (문서수)   ──┼──→ [플랫폼별 포화율 산출] ──→ [★★★ 황금 키워드]
  YouTube API (조회수)  ──┤        (공급 ÷ 수요)                │
  Kakao API (검색결과)  ──┘                                     ↓
                                                       [Gemini 2.5 Flash]
                                                                │
                                                                ↓
                                                     [플랫폼별 기획안 생성]
                                                     (네이버/유튜브/티스토리)
```

---

## 실제 성과 및 임팩트 | Results & Impact

> 💡 **진행 중인 성과 측정 (2026.03 기준)**
> AutoAuthor 파이프라인 도입 이후, 블로그 기획 프로세스를 효율화하고 실제 트래픽 성장을 측정하고 있습니다.

| 지표 (Metrics) | 도입 전 (Before) | 도입 후 (After) | 성장률/개선도 |
|---|---|---|---|
| **기획 소요 시간** | 1건당 약 60분 | 1건당 약 5분 이내 | **91% 단축** 🚀 |
| **타겟 유입량** | [Ex. 월간 1천 뷰] | [Ex. 월간 5천 뷰] | **[데이터 입력 대기]** |
| **상위 노출 포스트** | [Ex. 5 건] | [Ex. 15 건] | **[데이터 입력 대기]** |

*실제 데이터로 업데이트할 예정입니다.*

---

## 파일 구조 | File Structure

```
AutoAuthor/
├── README.md
├── LICENSE                            # MIT License
├── requirements.txt
├── mvforrest_seo_v3.py                # SEO 키워드 분석기 (CLI 지원)
├── mvforrest_seo_config.example.py    # API 키 설정 템플릿
├── content_planner.py                 # AI 기획안 자동 생성기 (풀 파이프라인)
├── profiles/
│   └── latest.json                    # 프로필 설정 예시
├── results/
│   └── sample_output.csv              # 샘플 분석 결과
└── docs/
    ├── usage_guide.md                 # 상세 사용 가이드
    └── 콘텐츠_성장_전략_가이드.md       # 채널 통합 성장 전략
```

---

## 빠른 시작 | Quick Start

### 1. 설치

```bash
git clone https://github.com/kimble125/AutoAuthor.git
cd AutoAuthor
pip install -r requirements.txt
```

### 2. API 키 설정

```bash
# config 파일 복사 후 API 키 입력
cp mvforrest_seo_config.example.py mvforrest_seo_config.py
```

```python
# mvforrest_seo_config.py
NAVER_CLIENT_ID = ""           # https://developers.naver.com 에서 발급
NAVER_CLIENT_SECRET = ""
USE_NAVER_OPENAPI = True
GEMINI_API_KEY = ""            # https://aistudio.google.com 에서 무료 발급
```

### 3. CLI 실행

```bash
# 단일 작품 분석
python mvforrest_seo_v3.py --seed "프리렌" --seed "장송의 프리렌"

# 두 키워드 비교 (정식 제목 vs 줄임말)
python mvforrest_seo_v3.py --seed "이 사랑 통역 되나요" --seed "이사통" --no-cross-mode

# 프로필 파일로 실행 (복잡한 설정 시)
python mvforrest_seo_v3.py --profile profiles/latest.json

# 크로스 키워드 모드 (두 주제를 엮는 키워드 발굴)
python mvforrest_seo_v3.py --cross-mode --cross-topic "계엄|영화 1987"

# AI 기획안까지 자동 생성 (풀 파이프라인)
python content_planner.py
```

### 4. 결과 확인

`output_preview/` 폴더에 CSV 파일과 텍스트 리포트가 자동 생성됩니다.

---

## CLI 옵션 | CLI Options

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--seed` | 시드 키워드 (반복 가능) | — |
| `--depth` | 롱테일 탐색 깊이 | 2 |
| `--min-words` | 최소 단어 수 | 1 |
| `--max-words` | 최대 단어 수 | 7 |
| `--profile` | JSON 프로필 파일 경로 | — |
| `--cross-mode` | 크로스 키워드 모드 활성화 | false |
| `--no-cross-mode` | 크로스 키워드 모드 비활성화 | — |
| `--cross-topic` | 크로스 토픽 (형식: `"주제A\|주제B"`) | — |
| `--request-delay` | 요청 간격 (초) | 0.5 |
| `--output-dir` | 결과 저장 디렉토리 | output_preview/ |

---

## 개발 철학 | Development Philosophy

AutoAuthor는 **"데이터가 주도하는 콘텐츠 원 소스 멀티 유즈(OSMU)"**를 지향합니다.
1. **정밀함(Precision)**: 프록시 데이터에 의존하지 않고, 실제 광고 API 수준의 검색 데이터를 활용합니다.
2. **효율성(Efficiency)**: 한 번의 분석으로 네이버, 유튜브, 인스타그램 등 여러 채널의 전략을 동시에 수립합니다.
3. **기회(Opportunity)**: 플랫폼 간의 데이터 격차를 포착하여, 남들이 보지 못하는 블루오션을 선점하게 돕습니다.

---

## AutoAuthor 등급 시스템 | Grading System

### 플랫폼별 포화율(Saturation Rate)
포화율은 **공급(문서수/영상수)을 수요(검색량/조회수)로 나눈 값**입니다. 이 값이 낮을수록 해당 시장의 기회는 큽니다.

| 등급 | 포화율 | 설명 |
|---|---|---|
| ★★★ (Golden) | ≤ 1% | 수요 대비 공급이 극도로 적음. 상위 노출 및 조회수 폭발 확정 |
| ★★ (Promising) | ≤ 10% | 경쟁이 어느 정도 있으나, 양질의 콘텐츠로 충분히 승산 있음 |
| ★ (Saturated) | > 10% | 이미 포착된 시장. 높은 체급이나 차별화된 니치 전략 필요 |

> **예시**: 네이버에서 ★★인 키워드가 유튜브에선 ★★★일 수 있습니다. 이 경우 해당 콘텐츠는 영상으로 제작하는 것이 유리합니다.

---

## AI 기획안 자동 생성 | Content Planner

`AutoAuthor`는 발굴된 **황금 키워드(★★★)**를 기반으로 플랫폼 맞춤형 기획안을 자동 생성합니다:

1. **네이버 블로그**: SEO 최적화 제목, H2-H3 구조, 메타 디스크립션 포함.
2. **유튜브**: 고클릭 유도 썸네일 컨셉, 시청 지속시간을 고려한 대본 스크립트.
3. **티스토리**: 애드센스 수익 극대화를 위한 정보성 글 구조 및 관련 키워드 배치.

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

| 콘텐츠명 | 월간검색량(네이버) | 키워드 | 블로그문서량 | 추천(네이버) | 유튜브영상수 | 평균조회수 | 추천(유튜브) |
|---|---|---|---|---|---|---|---|
| 프로젝트 헤일메리 | 1,544,500 | 해석/결말 | 841 | ★★★ | 398 | 143,044 | ★★★ |
| 마션 | 50,990 | 마션 결말 | 3,883 | ★★ | 11,615 | 1,282,810 | ★★★ |

---

## 웹 대시보드 | Web Dashboard

분석 결과를 팀과 공유할 수 있는 인터랙티브 대시보드:

**→ [Live Demo](https://seokeyword-qjyzzhbx.manus.space)**

#### 📸 대시보드 주요 스크린샷

> **UI 프리뷰** (아래 대괄호 영역을 실제 이미지 경로로 수정해 주세요)

![AutoAuthor 대시보드 메인 화면 - 화제성 매트릭스]([여기에_실제_이미지_경로_입력_예:assets/dashboard_main.png])
*황금 키워드를 발굴하여 한눈에 보여주는 핵심 매트릭스 UI*

![AI 기획안 자동 생성 화면]([여기에_실제_이미지_경로_입력_예:assets/dashboard_planner.png])
*Gemini 2.5 Pro가 즉시 발행 가능한 맞춤형 기획안 3종을 제안하는 화면*

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

- **Language:** Python 3.9+
- **AI:** Google Gemini 2.5 Flash / Pro API
- **Data Sources:** 
  - **Naver**: Search Ad API (수요), Search Blog OpenAPI (공급)
  - **YouTube**: Data API v3 (수요/공급)
  - **Other**: Google Suggest API, TMDB, WatchaPedia, Google News RSS
- **Web Dashboard:** React 19 + Tailwind CSS 4 + Recharts + shadcn/ui
- **Deployment:** GitHub Actions / Manus (manus.space)

---

## 활용 사례 | Use Cases

이 툴킷은 다음 블로그의 SEO 전략 수립에 실제로 활용되고 있습니다:

- **MVforrest 블로그:** [forrest125.tistory.com](https://forrest125.tistory.com) — 영화·드라마 심층 리뷰 (41편+)

---

## 로드맵 | Roadmap

- [x] V1: 구글 자동완성 기반 키워드 수집
- [x] V2: 네이버 경쟁도 측정 + 기회 점수 산출
- [x] V3: Gemini AI 연동 + CLI 인터페이스 + 프로필 시스템
- [x] V4: AutoAuthor 화제성 × 포화도 등급 시스템
- [x] V5: AI 기획안 자동 생성 (content_planner.py)
- [x] V6: **네이버 검색광고 API 통합 (고정밀 검색량 측정)**
- [x] V7: **유튜브 Data API v3 통합 (멀티 플랫폼 스코어링)**
- [ ] V8: 카카오/티스토리 통합 및 자동 포스팅 연동
- [ ] V9: SQLite 적재 + 대시보드 고도화

---

## 라이선스 | License

MIT License — 자유롭게 사용, 수정, 배포 가능합니다.

---

*Made with data-driven passion by [kimble125](https://github.com/kimble125) | [Blog](https://forrest125.tistory.com)*
