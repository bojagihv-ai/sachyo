from src.adapters import build_adapters


def test_registry_includes_main_sources():
    all_sources = ["coupang", "naver", "11st", "gmarket", "auction", "ssg", "lotteon", "wemakeprice", "tmon", "interpark", "unknown"]
    adapters, unsupported = build_adapters(all_sources, max_candidates=5)
    names = [a.source_name for a in adapters]
    for src in ["coupang", "naver", "11st", "gmarket", "auction", "ssg", "lotteon", "wemakeprice", "tmon", "interpark"]:
        assert src in names
    assert "unknown" in unsupported
