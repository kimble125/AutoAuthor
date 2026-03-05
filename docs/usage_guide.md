# 사용 가이드 | Usage Guide

## 초보자를 위한 단계별 설치 및 실행 방법

### Step 1. Python 설치 확인

```bash
python --version  # Python 3.8 이상이어야 합니다
```

### Step 2. 리포지토리 클론

```bash
git clone https://github.com/kimble125/AutoAuthor.git
cd content-trend-seo-toolkit
```

### Step 3. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### Step 4. Gemini API 키 발급

- 1. [Google AI Studio](https://aistudio.google.com/) 접속
- 2. 우측 상단 **Get API key** 클릭
- 3. **Create API key** → 키 복사

### Step 5. 코드 설정

`mvforrest_seo_v3.py` 파일을 열고 상단 CONFIG 부분을 수정합니다:

```python
# ── [CONFIG] 여기만 수정하면 됩니다 ──
GEMINI_API_KEY = "여기에_API_키_붙여넣기"
SEED_KEYWORDS = ["분석할 영화 제목", "드라마 제목"]
```

### Step 6. 실행

```bash
python mvforrest_seo_v3.py
```

### Step 7. 결과 확인

`results/` 폴더에 다음 파일들이 생성됩니다:

- `keyword_opportunity_날짜시간.csv` — 전체 키워드 분석 결과
- `keyword_report_날짜시간.txt` — 요약 리포트

## 기회 점수 해석 방법

| 점수 | 등급 | 의미 | 전략 |
|---|---|---|---|
| 50+ | 🔥 황금 키워드 | 수요 있음 + 경쟁 거의 없음 | 제목에 반드시 포함 |
| 20~49 | 👀 유망 키워드 | 경쟁이 낮아 노려볼 만함 | 소제목(H2)에 활용 |
| 10~19 | ⚠️ 보통 | 어느 정도 경쟁 있음 | 본문에만 자연스럽게 |
| 0~9 | 💤 레드오션 | 이미 포화 상태 | 사용 자제 |

## 크로스 키워드 모드 (여러 작품 조합)

시의성 이슈와 여러 작품을 연결하는 키워드를 찾을 때:

```python
CROSS_MODE = True
CROSS_KEYWORDS = [
    ("계엄", "영화 1987"),
    ("계엄", "그것이 알고싶다"),
    ("서울의 봄", "영화 1987"),
]
```

**제목 공식:**

`[이슈 키워드] + [작품A] + [작품B] + [연결 포인트]`
예: `"계엄 선포 후 다시 보는 영화 1987 | 그것이 알고싶다가 짚은 역사의 반복"`
