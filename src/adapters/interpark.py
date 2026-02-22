from __future__ import annotations

import re
from urllib.parse import quote

from src.adapters.base import BaseAdapter
from src.adapters.coupang import _fetch_page_text, _first_match, _strip_html, _to_num
from src.core.models import ListingCandidate, ListingMeta


class InterparkAdapter(BaseAdapter):
    source_name = "interpark"

    async def search_by_image(self, context, image_path: str, query_hint: str | None) -> list[ListingCandidate]:
        if not query_hint or context is None:
            return []
        page = await context.new_page()
        url = f"https://isearch.interpark.com/isearch?q={quote(query_hint)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        await page.wait_for_timeout(1200)
        html = await page.content()
        await page.close()

        candidates=[]
        rank=0
        for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
            href = m.group(1)
            title = _strip_html(m.group(2))
            if len(title) < 4:
                continue
            if href.startswith("/"):
                href = f"https://shopping.interpark.com{href}"
            if not href.startswith("http"):
                continue
            rank += 1
            if rank > self.max_candidates:
                break
            item_id = re.sub(r"\W+", "_", href)[-30:] or f"ip_{rank}"
            candidates.append(ListingCandidate(platform=self.source_name,item_id=item_id,url=href,title=title,source_rank=rank,source_query=query_hint,extracted_evidence="search_html"))
        return candidates

    async def enrich_listing(self, context, listing_url: str) -> ListingMeta:
        text = await _fetch_page_text(context, listing_url, timeout_ms=self.timeout_ms)
        price = _to_num(_first_match(text, r"([0-9,]+)\s*원"))
        review = _to_num(_first_match(text, r"리뷰\s*([0-9,]+)"))
        return ListingMeta(price_min=price, price_max=price, review_count=int(review) if review else None, views_estimated=review)
