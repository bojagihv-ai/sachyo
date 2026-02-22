from __future__ import annotations

from pathlib import Path

from src.adapters.base import BaseAdapter
from src.core.models import DownloadResult, ListingCandidate, ListingMeta


class DemoAdapter(BaseAdapter):
    source_name = "demo"
    needs_browser = False

    async def search_by_image(self, context, image_path: str, query_hint: str | None) -> list[ListingCandidate]:
        q = query_hint or Path(image_path).stem
        return [
            ListingCandidate(
                platform="demo",
                item_id="demo_001",
                url="https://example.com/demo-item-1",
                title=f"{q} 샘플 상품 1",
                image_url=None,
                source_rank=1,
                source_query=q,
                extracted_evidence="demo_seed",
            ),
            ListingCandidate(
                platform="demo",
                item_id="demo_002",
                url="https://example.com/demo-item-2",
                title=f"{q} 샘플 상품 2",
                image_url=None,
                source_rank=2,
                source_query=q,
                extracted_evidence="demo_seed",
            ),
        ]

    async def enrich_listing(self, context, listing_url: str) -> ListingMeta:
        return ListingMeta(price_min=19900, price_max=24900, rating=4.5, review_count=128, sales_index=320, views_estimated=128)

    async def crawl_detail_images(self, context, listing_url: str, save_dir: Path, save_snapshot: bool = True) -> DownloadResult:
        img = save_dir / "detail_0000.jpg"
        img.write_bytes(b"demo-image")
        snapshot = None
        if save_snapshot:
            snapshot = save_dir / "page_snapshot.html"
            snapshot.write_text(f"<html><body>demo: {listing_url}</body></html>", encoding="utf-8")
        return DownloadResult(
            extracted_urls=["local://demo/detail_0000.jpg"],
            downloaded_files=[str(img)],
            failed_urls=[],
            page_snapshot_html=str(snapshot) if snapshot else None,
            page_full_png=None,
        )
