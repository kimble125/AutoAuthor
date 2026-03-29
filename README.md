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

## 시스템 아키텍처 | Core Architecture

비용과 효율을 극대화한 **2-Pass 지연 평가(Lazy Evaluation) 아키텍처**를 채택했습니다.

```
[데이터 발굴 레이어]
  TMDB / WatchaPedia ─────┐
  Google News RSS    ─────┼──→ [발굴된 시드 키워드 (최대 30개)] ──┐
  Google Suggest     ─────┘                                   │
                                                              ↓
[1차 필터링 (비용 최소화)] ← [대규모 시장 수요 및 블로그 공급 측정]
  Naver Ad API (검색량)    ──┐       
  Google Trends API (가중치)─┼──→ [통합 수요 산출] 
  Naver Blog (문서수)      ──┼──→ [네이버/티스토리 포화도 랭킹] ──┐
  Kakao API (검색결과)     ──┘                                   │
                                                              │ (Top 5 추출)
[2차 지연 평가 (고정밀)] ← [알짜 키워드 특화 분석]                 │
  YouTube API (에버그린 조회수) ───←──────────────────────────────┘
  YouTube API (트렌디 30일 영상수) ──→ [유튜브 포화율 산출 및 ★★★ 판별]
                                                          │
                                                          ↓
[Synergy Content Engine]  ← [Gemini 2.5 Pro / Flash]
  개별 플랫폼 기획안 생성 (네이버/티스토리/유튜브 등)
  다중 작품 연계 시너지(허브) 기획안 자동 생성 (OSMU 체류시간 극대화)
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
├── autoauthor/                        # 코어 패키지 모듈
│   ├── pipeline.py                    # 메인 실행 파이프라인 엔진 (V8)
│   ├── sources/                       # 데이터 수집 채널 (각 리포트 추적)
│   ├── ai/                            # Gemini 2.5 AI 통합 레이어
│   └── planner/                       # 기획안 생성 및 템플릿 관리 모듈
├── .env.example                       # API 키 환경 변수 예시
└── results/                           # 각종 CSV 및 기획안(.md) 출력물 저장소
```

---

### 1. 설치 (Installation)

```bash
git clone https://github.com/kimble125/AutoAuthor.git
cd AutoAuthor
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env)

프로젝트 루트에 `.env` 파일을 생성하고 아래 API 키를 입력합니다.
*(API 할당량 초과 방지를 위해 여러 개의 유튜브 키를 활용할 수 있습니다.)*

```env
NAVER_CLIENT_ID="발급받은 ID"
NAVER_CLIENT_SECRET="발급받은 Secret"
KAKAO_API_KEY="Kakao REST API 키"
YOUTUBE_API_KEY="Google Cloud 키"
GEMINI_API_KEY="Google AI Studio 키"
```

### 3. CLI 실행 (Execution)

AutoAuthor 파이프라인은 모듈화된 명령어로 가장 쉽고 강력하게 작동합니다.

```bash
# 수동 타겟 분석 (기획안 자동 `.md` 파일 저장)
python3 -m autoauthor --titles "마션, 인터스텔라, 그래비티"

# 타겟 플랫폼 지정 및 연계 시너지 기획
python3 -m autoauthor --titles "마션, 인터스텔라" --platforms "tistory,youtube,synergy"

# 전자동 트렌드 탐지 및 기획 (Autopilot)
python3 -m autoauthor --mode autopilot --top 5
```

### 4. 결과 출력 (Output)

실행이 완료되면 `results/` 폴더에 아래의 에셋들이 자동 구성됩니다.
*   `키워드분석_통합_수동분석_YYYYMMDD.csv` (데이터 리포트)
*   `기획안_마션_tistory_YYYYMMDD.md` (개별 플랫폼 기획안)
*   `기획안__통합__3개_작품_연계_추천_가이드_synergy.md` (내부링크 연계 허브 기획안)
---

## CLI 옵션 | CLI Options

| 변수명 | 필수 여부 | 설명 | 기본값 |
|---|---|---|---|
| `--mode` | 선택 | 실행 모드. `autopilot`(자동 트렌드 기반) 또는 `copilot` | `autopilot` |
| `--category` | 선택 | 분석 카테고리 (예: `movie`, `drama`) | `movie` |
| `--top` | 선택 | autopilot 모드 시 상위 몇 개의 트렌드를 검색할지 지정 | `3` |
| `--platforms` | 선택 | 기획안을 생성할 타겟 플랫폼 (콤마로 다중 선택 가능) <br>지원: `tistory, naver, youtube, instagram, facebook, shortform, thread, synergy` | `tistory` |
| `--titles` | 선택 | 트렌드 탐지를 스킵하고 원하는 작품명 수동 지정 <br>예: `"프로젝트 헤일메리, 마션"`| — |

---

## 개발 철학 | Development Philosophy (For 1-Person Business Marketer)

AutoAuthor는 1인 마케터의 **최대 효율(OSMU)과 한정된 리소스 관리**를 지향하며 아래 3원칙으로 설계되었습니다.

1. **지능형 비용 제어 (Intelligent Lazy Evaluation)**
   - 유튜브 API의 `10,000` 쿼터 한도 문제를 회피하기 위해 무차별 탐색을 폐기. 무료인 네이버 블로그 문서량으로 시장을 1단계 필터링하고, 잠재력 있는 상위 5개 키워드만 정밀 평가하는 **2-Pass 지연 평가(Lazy Evaluation)** 아키텍처로 API 소모 비용을 83% 감축했습니다.

2. **단기 바이럴과 장기 수익의 투 트랙 (Trendy vs Evergreen)**
   - 오늘 당장 터지는 키워드(최근 30일 데이터 + Google Trends 지수)와 영원히 읽히는 롱테일 키워드(유튜브 통합 조회수 + 블로그 누적 문서)를 이중으로 분석하여, 가장 공격적이고 단단한 수익 파이프라인 밸런스를 구축합니다.

3. **연계 로직 (Synergy Content Engine)**
   - 점 단위의 정보가 아니라 '선' 단위의 흐름을 짭니다. 여러 작품을 동시에 분석하면 이를 하나로 관통하는 메가 테마를 도출하고, 각각의 개별 문서끼리 내부 링크(Internal Linking) 할 수 있도록 기획부터 **SEO 허브 구조**를 설계하여 체류 시간을 극대화합니다.

---

## AutoAuthor 등급 시스템 | Grading System

### ⚠️ 중요 주의사항: YouTube API 일일 할당량(Quota) 제한

AutoAuthor의 유튜브 지표 수집(에버그린/트렌디 투 트랙 전략)은 구글 클라우드의 YouTube Data API를 사용합니다.
- **일일 무료 제공량**: 10,000 할당량(Quota Units)
- **1키워드 당 소모량**: 200 할당량 (누적 검색 100 + 최근 30일 검색 100)
- **우회 전략 (Lazy Evaluation)**: 비용 폭탄을 막기 위해 네이버 블로그 검색으로 먼저 포화도를 판별하고 가장 추천할만 한(블루오션인) **상위 5개의 키워드에 대해서만 제한적으로 유튜브 검색을 실행**합니다. (하루 최대 10개 영화 세트 분석 가능)
- **만약 결과에 유튜브 추천도나 조회수가 하이픈(-) 또는 0으로 나온다면?**:
  이는 에러가 아니라 **일일 10,000 쿼터 한도를 모두 소진했기 때문**입니다. 당황하지 마시고, 제한이 리셋되는 다음 날 오전(태평양 표준시 자정 기준)에 다시 시도하거나 구글 클라우드 콘솔에서 API Key를 추가 발급받아 환경 변수(`.env`)를 교체하시면 됩니다.
  나머지 하위 순위 키워드들에 대해서는 조회 자체를 생략하므로 `(조회 생략)` 기호로 표기됩니다.

---
## 설치 및 설정 (Installation & Setup)
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
