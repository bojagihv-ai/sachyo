from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from src.core.logging_utils import setup_logger
from src.core.models import RunConfig
from src.core.pipeline import run_pipeline_sync
from src.ui.config_store import load_ui_config, save_ui_config



def _read_csv_preview(path: Path):
    import csv

    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 49:
                break
    return rows
st.set_page_config(page_title="Sachyo Pro", layout="wide")
st.title("Sachyo Pro - 제품 이미지 기반 리스팅 탐색")
st.caption("초보자도 쉽게 사용할 수 있는 운영형 UI")

saved = load_ui_config()

with st.sidebar:
    st.header("실행 설정")
    image_path = st.text_input("입력 이미지 경로", value=saved.get("image_path", ""), help="예: C:/data/input.jpg")
    query_hint = st.text_input("제품명/모델명 힌트", value=saved.get("query_hint", ""))
    output_dir = st.text_input("출력 폴더", value=saved.get("output_dir", "./output"))
    max_candidates = st.number_input("소스당 후보 수", min_value=1, max_value=200, value=int(saved.get("max_candidates_per_source", 30)))
    topk_final = st.number_input("최종 상위 후보 수", min_value=1, max_value=300, value=int(saved.get("topk_final", 50)))
    manual_topn = st.number_input("수동검수 리포트 Top N", min_value=1, max_value=200, value=int(saved.get("manual_review_topn", 30)))

    st.subheader("소스 선택")
    source_options = ["coupang", "naver", "11st", "gmarket", "auction", "ssg", "lotteon", "wemakeprice", "tmon", "interpark", "demo"]
    default_sources = saved.get("sources", ["coupang", "naver"])
    sources = st.multiselect("활성 소스", source_options, default=default_sources)

    st.subheader("API 키 / 토큰")
    openai_api_key = st.text_input("OPENAI_API_KEY", value=saved.get("OPENAI_API_KEY", ""), type="password")
    naver_api_key = st.text_input("NAVER_API_KEY", value=saved.get("NAVER_API_KEY", ""), type="password")
    custom_api_endpoint = st.text_input("CUSTOM_API_ENDPOINT", value=saved.get("CUSTOM_API_ENDPOINT", ""))

    save_btn = st.button("설정 저장")
    if save_btn:
        save_ui_config(
            {
                "image_path": image_path,
                "query_hint": query_hint,
                "output_dir": output_dir,
                "max_candidates_per_source": int(max_candidates),
                "topk_final": int(topk_final),
                "manual_review_topn": int(manual_topn),
                "sources": sources,
                "OPENAI_API_KEY": openai_api_key,
                "NAVER_API_KEY": naver_api_key,
                "CUSTOM_API_ENDPOINT": custom_api_endpoint,
            }
        )
        st.success("설정 저장 완료")

run_btn = st.button("실행 시작", type="primary", use_container_width=True)

if run_btn:
    if not image_path:
        st.error("입력 이미지 경로를 입력하세요.")
        st.stop()

    img = Path(image_path)
    if not img.exists():
        st.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        st.stop()

    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["NAVER_API_KEY"] = naver_api_key
    os.environ["CUSTOM_API_ENDPOINT"] = custom_api_endpoint

    config = RunConfig(
        image=str(img),
        query_hint=query_hint or None,
        max_candidates_per_source=int(max_candidates),
        topk_final=int(topk_final),
        sources=sources or ["demo"],
        output_dir=output_dir,
        create_xlsx=False,
        save_snapshots=True,
        manual_review_topn=int(manual_topn),
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger = setup_logger(Path(output_dir) / "latest.log")

    with st.spinner("파이프라인 실행 중..."):
        result = run_pipeline_sync(config, logger)

    st.success("실행 완료")

    c1, c2, c3 = st.columns(3)
    c1.metric("run_id", result["run_id"])
    c2.metric("후보 수", result["count"])
    c3.metric("진행률", f"{result['completion_percent']}%")

    st.write("완료 범위:", result["completed_scope"])
    st.write("구현 소스:", ", ".join(result.get("implemented_sources", [])))
    if result.get("unsupported_sources"):
        st.warning(f"미지원/스킵 소스: {', '.join(result['unsupported_sources'])}")

    if result["is_complete"]:
        st.info("최종완성 상태입니다.")
    else:
        st.warning("중간 완성 상태입니다. 다음 작업:")
        for i, task in enumerate(result.get("next_tasks", []), start=1):
            st.write(f"{i}. {task}")

    run_root = Path(result["paths"]["run_root"])
    st.write("결과 경로:", str(run_root))

    reports = run_root / "reports"
    candidates = reports / "candidates.csv"
    verified = reports / "verified.csv"
    leaderboard = reports / "leaderboards.csv"

    if candidates.exists():
        st.subheader("Candidates Preview")
        st.dataframe(_read_csv_preview(candidates), use_container_width=True)
    if verified.exists():
        st.subheader("Verified Preview")
        st.dataframe(_read_csv_preview(verified), use_container_width=True)
    if leaderboard.exists():
        st.subheader("Leaderboards Preview")
        st.dataframe(_read_csv_preview(leaderboard), use_container_width=True)


