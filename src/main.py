from __future__ import annotations

from pathlib import Path
import argparse

from src.core.logging_utils import setup_logger
from src.core.models import RunConfig
from src.core.pipeline import run_pipeline_sync


def _run(config: RunConfig):
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    logger = setup_logger(Path(config.output_dir) / "latest.log")
    result = run_pipeline_sync(config, logger)

    print(f"실행 완료: run_id={result['run_id']}, 후보수={result['count']}")
    print(f"진행률: {result['completion_percent']}% | 범위: {result['completed_scope']}")

    if result["is_complete"]:
        print("완성 상태입니다. 실행 방법은 README의 설치/실행 섹션을 참고하세요.")
    else:
        print("중간 완성 상태입니다. 다음 작업:")
        for idx, task in enumerate(result["next_tasks"], start=1):
            print(f"  {idx}. {task}")
        print("다음 작업을 진행할까요?")

    print(f"결과 경로: {result['paths']['run_root']}")


def _build_config_from_args(args) -> RunConfig:
    return RunConfig(
        image=args.image,
        query_hint=args.query_hint or None,
        max_candidates_per_source=args.max_candidates_per_source,
        topk_final=args.topk_final,
        sources=[x.strip() for x in args.sources.split(",") if x.strip()],
        output_dir=args.output_dir,
        create_xlsx=args.xlsx,
        save_snapshots=args.save_snapshots,
        manual_review_topn=args.manual_review_topn,
    )


def main():
    parser = argparse.ArgumentParser(description="Image-based Korean shopping listing explorer")
    sub = parser.add_subparsers(dest="cmd")
    run_p = sub.add_parser("run")
    run_p.add_argument("--image", required=True)
    run_p.add_argument("--query_hint", default="")
    run_p.add_argument("--max_candidates_per_source", type=int, default=30)
    run_p.add_argument("--topk_final", type=int, default=50)
    run_p.add_argument("--sources", default="coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark")
    run_p.add_argument("--output_dir", default="./output")
    run_p.add_argument("--xlsx", action="store_true")
    run_p.add_argument("--save_snapshots", action="store_true", default=True)
    run_p.add_argument("--manual_review_topn", type=int, default=30)

    args = parser.parse_args()
    if args.cmd != "run":
        parser.print_help()
        return
    _run(_build_config_from_args(args))


if __name__ == "__main__":
    main()
