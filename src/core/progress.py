from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProgressSummary:
    completion_percent: int
    completed_scope: str
    is_complete: bool
    next_tasks: list[str]


def summarize_progress(active_sources: list[str], implemented_sources: list[str]) -> ProgressSummary:
    required_sources = {"coupang", "naver", "11st", "gmarket", "auction", "ssg", "lotteon", "wemakeprice", "tmon", "interpark"}
    implemented = set(implemented_sources)

    mvp_done = {"coupang", "naver"}.issubset(implemented)
    implemented_required = len(required_sources & implemented)
    source_ratio = min(implemented_required / len(required_sources), 1.0)
    base = 70 if mvp_done else 40
    completion = int(round(base + source_ratio * 30))

    is_complete = required_sources.issubset(implemented)

    roadmap = [
        ("11st", "11번가 Adapter 구현(search/enrich/detail crawl)"),
        ("gmarket", "G마켓 Adapter 구현"),
        ("auction", "옥션 Adapter 구현"),
        ("ssg", "SSG Adapter 구현"),
        ("lotteon", "롯데ON Adapter 구현"),
        ("wemakeprice", "위메프 Adapter 구현"),
        ("tmon", "티몬 Adapter 구현"),
        ("interpark", "인터파크 Adapter 구현"),
    ]

    if is_complete:
        completed_scope = "요구된 10개 소스 확장 목표까지 완료"
        next_tasks: list[str] = []
    else:
        completed_scope = "MVP(쿠팡/네이버) + 확장 가능한 10소스 구조 완료"
        next_tasks = [msg for key, msg in roadmap if key not in implemented]
        next_tasks.append("OCR/리뷰 NLP/옵션 비교 정밀도 고도화")

    return ProgressSummary(
        completion_percent=max(0, min(100, completion)),
        completed_scope=completed_scope,
        is_complete=is_complete,
        next_tasks=next_tasks,
    )
