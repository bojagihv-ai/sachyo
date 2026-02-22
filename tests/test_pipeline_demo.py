from pathlib import Path

from src.core.logging_utils import setup_logger
from src.core.models import RunConfig
from src.core.pipeline import run_pipeline_sync


def test_pipeline_demo_end_to_end(tmp_path: Path):
    image = tmp_path / "input.jpg"
    image.write_bytes(b"abc123")

    out = tmp_path / "out"
    out.mkdir()
    logger = setup_logger(out / "latest.log")

    config = RunConfig(
        image=str(image),
        query_hint="테스트",
        sources=["demo"],
        output_dir=str(out),
        topk_final=5,
    )
    result = run_pipeline_sync(config, logger)
    assert result["count"] == 2

    run_root = Path(result["paths"]["run_root"])
    assert (run_root / "reports" / "candidates.csv").exists()
    assert (run_root / "reports" / "leaderboards.csv").exists()
