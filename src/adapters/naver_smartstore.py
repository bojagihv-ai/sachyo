from __future__ import annotations

import re
from urllib.parse import quote

from src.adapters.base import BaseAdapter
from src.adapters.coupang import _fetch_page_text, _first_match, _strip_html, _to_num
from src.core.models import ListingCandidate, ListingMeta


class NaverSmartstoreAdapter(BaseAdapter):
    source_name = "naver"

    async def search_by_image(self, context, image_path: str, query_hint: str | None) -> list[ListingCandidate]:
        if not query_hint or context is None:
            return []
        page = await context.new_page()
        url = f"https://search.shopping.naver.com/search/all?query={quote(query_hint)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        await page.wait_for_timeout(1000)
        html = await page.content()
        await page.close()

        candidates = []
        pattern = re.compile(r'<a[^>]+class="product_link__TrAac"[^>]+href="([^"]+)"[^>]*>.*?<div[^>]+class="product_title__Mmw2K"[^>]*>(.*?)</div>', re.S)
        for rank, m in enumerate(pattern.finditer(html), start=1):
            if rank > self.max_candidates:
                break
            href = m.group(1)
            title = _strip_html(m.group(2))
            item_id = re.sub(r"\W+", "_", href or "")[-30:] or f"nv_{rank}"
            candidates.append(ListingCandidate(platform=self.source_name, item_id=item_id, url=href, title=title, source_rank=rank, source_query=query_hint, extracted_evidence="search_html"))
        return candidates

    async def enrich_listing(self, context, listing_url: str) -> ListingMeta:
        text = await _fetch_page_text(context, listing_url, timeout_ms=self.timeout_ms)
        price = _to_num(_first_match(text, r"([0-9,]+)\s*원"))
        rating = _to_num(_first_match(text, r"평점\s*([0-9.]+)"))
        review = _to_num(_first_match(text, r"리뷰\s*([0-9,]+)"))
        return ListingMeta(price_min=price, price_max=price, rating=rating, review_count=int(review) if review else None, views_estimated=review)
