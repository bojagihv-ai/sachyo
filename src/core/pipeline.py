from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.request import Request, urlopen

from src.adapters import build_adapters
from src.core.models import CandidateRecord, DownloadResult, ListingMeta, RunConfig
from src.core.progress import summarize_progress
from src.core.report import write_manual_review_html, write_reports
from src.core.similarity import compare_images
from src.core.storage import ensure_run_dirs, listing_asset_dirs, make_run_id, save_run_config
from src.core.verify import verify_candidate

try:
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover
    def tqdm(x, **kwargs):
        return x


async def run_pipeline(config: RunConfig, logger) -> dict:
    run_id = make_run_id(config.image, config.query_hint)
    dirs = ensure_run_dirs(config.output_dir, run_id)
    save_run_config(dirs["root"], config.__dict__)

    adapters, unsupported = build_adapters(config.sources, config.max_candidates_per_source)
    if unsupported:
        logger.warning(f"Unsupported adapters skipped: {unsupported}")

    browser = None
    context = None
    records: list[CandidateRecord] = []

    if any(getattr(a, "needs_browser", True) for a in adapters):
        try:
            from playwright.async_api import async_playwright

            p = await async_playwright().start()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 2200})
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Playwright unavailable; browser-based adapters may be skipped: {e}")
            context = None
            p = None
    else:
        p = None

    try:
        for adapter in adapters:
            if getattr(adapter, "needs_browser", True) and context is None:
                logger.error(f"skip source={adapter.source_name} reason=browser_unavailable")
                continue

            logger.info(f"Searching source={adapter.source_name}")
            try:
                candidates = await adapter.search_by_image(context, config.image, config.query_hint)
            except Exception as e:  # noqa: BLE001
                logger.error(f"search_by_image failed source={adapter.source_name} err={e}")
                continue

            for c in tqdm(candidates, desc=f"{adapter.source_name} candidates"):
                try:
                    meta = await adapter.enrich_listing(context, c.url)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"enrich failed url={c.url} err={e}")
                    meta = ListingMeta()

                asset_dirs = listing_asset_dirs(dirs["assets"], c.platform, c.item_id)
                main_image = _fetch_candidate_main_image(c.image_url, asset_dirs["main_images"], c.item_id)
                sim = compare_images(config.image, main_image, config.query_hint or "", c.title, config.query_hint)

                try:
                    download_result = await adapter.crawl_detail_images(context, c.url, asset_dirs["detail_images"], save_snapshot=config.save_snapshots)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"crawl_detail_images failed url={c.url} err={e}")
                    download_result = DownloadResult(failed_urls=[f"crawl_error:{e}"])

                verification = verify_candidate(config.query_hint or "", c, meta, sim)
                records.append(CandidateRecord(candidate=c, meta=meta, similarity=sim, verification=verification, download=download_result))
    finally:
        if context is not None:
            await context.close()
        if browser is not None:
            await browser.close()
        if p is not None:
            await p.stop()

    records = sorted(records, key=lambda r: (r.verification.confidence, r.similarity.score), reverse=True)[: config.topk_final]
    paths = write_reports(records, dirs["reports"], create_xlsx=config.create_xlsx)
    manual = write_manual_review_html(records, dirs["reports"] / "manual_review.html", topn=config.manual_review_topn)
    paths["manual_review"] = manual
    paths["run_root"] = dirs["root"]

    implemented_sources = [a.source_name for a in adapters]
    progress = summarize_progress(config.sources, implemented_sources)
    return {
        "run_id": run_id,
        "paths": paths,
        "count": len(records),
        "implemented_sources": implemented_sources,
        "unsupported_sources": unsupported,
        "completion_percent": progress.completion_percent,
        "completed_scope": progress.completed_scope,
        "is_complete": progress.is_complete,
        "next_tasks": progress.next_tasks,
    }


def _fetch_candidate_main_image(image_url: str | None, out_dir: Path, item_id: str) -> str:
    fallback = out_dir / f"{item_id}_fallback.bin"
    if not fallback.exists():
        fallback.write_bytes(b"fallback")
    if not image_url:
        return str(fallback)

    try:
        req = Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            suffix = Path(image_url.split("?")[0]).suffix or ".jpg"
            target = out_dir / f"{item_id}{suffix}"
            target.write_bytes(resp.read())
            return str(target)
    except Exception:  # noqa: BLE001
        return str(fallback)


def run_pipeline_sync(config: RunConfig, logger) -> dict:
    return asyncio.run(run_pipeline(config, logger))
