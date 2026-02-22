from src.core.progress import summarize_progress


def test_progress_mvp_partial():
    p = summarize_progress(
        ["coupang", "naver", "11st"],
        ["coupang", "naver"],
    )
    assert p.completion_percent >= 70
    assert p.is_complete is False
    assert any("11번가" in x for x in p.next_tasks)


def test_progress_hides_completed_11st_task():
    p = summarize_progress(
        ["coupang", "naver", "11st"],
        ["coupang", "naver", "11st"],
    )
    assert all("11번가" not in x for x in p.next_tasks)


def test_progress_complete_when_all_10_sources_implemented():
    implemented = ["coupang", "naver", "11st", "gmarket", "auction", "ssg", "lotteon", "wemakeprice", "tmon", "interpark", "demo"]
    p = summarize_progress(implemented, implemented)
    assert p.is_complete is True
    assert p.completion_percent == 100
    assert p.next_tasks == []
