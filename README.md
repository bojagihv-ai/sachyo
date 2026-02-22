# sachyo

제품 이미지 1장을 입력받아 국내 쇼핑몰 후보 리스팅을 탐색하고, 동일제품 판별/검수 후 CSV 리포트와 상세페이지 이미지 아카이브를 생성하는 Python 프로그램입니다.

## 설계 요약

### 데이터 스키마
- `RunConfig`: 실행 설정(입력 이미지, 소스 목록, 출력 경로, top-k 등)
- `ListingCandidate`: 검색 단계 후보(플랫폼, 링크, 타이틀, 대표 이미지 URL)
- `ListingMeta`: 가격/리뷰/평점/옵션/판매지표 등 메타
- `SimilarityResult`: pHash/dHash/SSIM/embedding-like/텍스트 유사도 + 3단계 클래스
- `VerificationResult`: 10단계 체크리스트 pass/fail + confidence + 사유
- `CandidateRecord`: 최종 단일 레코드(후보+메타+유사도+검수+다운로드 결과)

### 클래스/모듈
- `src/adapters/base.py`: Adapter 인터페이스, 공통 상세이미지 추출/다운로드 로직
- `src/adapters/coupang.py`: Coupang 검색/메타 수집
- `src/adapters/naver_smartstore.py`: 네이버쇼핑/스마트스토어 검색/메타 수집
- `src/core/similarity.py`: 이미지 유사도 계산 + 3단계 분류
- `src/core/verify.py`: 동일제품 10단계 자동 검수
- `src/core/report.py`: `candidates.csv`, `verified.csv`, `leaderboards.csv`, 수동검수 HTML
- `src/core/pipeline.py`: end-to-end 실행 파이프라인
- `src/main.py`: Typer CLI

### 실행 흐름
1. `run_id` 생성 + `run_config.json` 저장
2. 소스별 Adapter 검색(`search_by_image`)
3. 후보별 메타 수집(`enrich_listing`)
4. 대표 이미지 다운로드 후 유사도 계산 + 3단계 분류
5. 상세페이지 렌더링(Playwright) 후 모든 이미지 URL 추출/다운로드
6. 10단계 검수로 `verified_flag`, `confidence` 계산
7. CSV 3종 + (옵션) XLSX + 수동검수 HTML 생성

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m playwright install chromium
```

## 실행
```bash
python -m src.main run \
  --image ./input.jpg \
  --query_hint "제품명 모델명" \
  --sources coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark \
  --output_dir ./output
```


## 완료도/다음작업 안내(실행 후 출력)
- 실행이 끝나면 CLI가 자동으로 다음 정보를 출력합니다.
  - 현재 수행 범위와 진행률(%)
  - 완성 여부(`is_complete`)
  - 완성 시: 실행 가이드 안내
  - 중간 완성 시: 다음 작업 목록 + `다음 작업을 진행할까요?` 문구



## 운영용 UI 실행 (Streamlit)
초보자도 사용할 수 있도록 실행형 UI를 제공합니다.

```bash
pip install -e .[ui]
streamlit run src/ui/app.py
```

UI 기능:
- 이미지 경로/소스/후보수/출력폴더 설정
- API 키 입력(`OPENAI_API_KEY`, `NAVER_API_KEY`, `CUSTOM_API_ENDPOINT`) 및 저장
- 실행 결과(진행률/완료도/리포트 CSV 미리보기) 확인

## 출력 구조
```text
output/{run_id}/
  run_config.json
  reports/
    candidates.csv
    verified.csv
    leaderboards.csv
    manual_review.html
  assets/{platform}/{item_id}/
    main_images/
    detail_images/
      detail_0000.jpg
      ...
      page_snapshot.html
      page_full.png
```

## 정책/준수사항
- 공식 API 우선, 부재 시 제한적 렌더링 크롤링 사용
- robots/ToS 존중 및 rate-limit + retry + backoff 적용
- 로그인/결제/봇회피/캡차우회 미구현
- 각 후보는 URL 필수 저장, 가능하면 대표이미지 URL 및 추출근거 보존

## 확장 포인트
- `src/adapters/__init__.py`에 신규 Adapter 클래스 등록 시 소스 확장 가능
- 현재 구현: `demo`, `coupang`, `naver`, `11st(기본)`, `gmarket(기본)`, `auction(기본)`, `ssg(기본)`, `lotteon(기본)`, `wemakeprice(기본)`, `tmon(기본)`, `interpark(기본)`
- 나머지 소스는 동일 인터페이스로 순차 추가 가능


## 빠른 동작 확인(Demo 모드)
외부 의존성(Playwright/bs4/pandas 등) 설치가 어려운 환경에서도 `demo` 소스로 파이프라인 E2E 동작을 확인할 수 있습니다.

```bash
python -m src.main run --image ./input.jpg --query_hint "테스트" --sources demo --output_dir ./output_demo
```

## 실서비스 소스 테스트 전 체크
- `coupang/naver` 사용 시 `playwright` 및 Chromium 설치가 필요합니다.
- 설치 불가 환경에서는 프로그램이 자동으로 해당 소스를 skip하고 로그에 사유를 남깁니다.
