from __future__ import annotations

import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.adapters.base import BaseAdapter
from src.core.models import ListingCandidate, ListingMeta


class CoupangAdapter(BaseAdapter):
    source_name = "coupang"

    async def search_by_image(self, context, image_path: str, query_hint: str | None) -> list[ListingCandidate]:
        if not query_hint or context is None:
            return []
        page = await context.new_page()
        url = f"https://www.coupang.com/np/search?q={quote(query_hint)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        html = await page.content()
        await page.close()

        candidates: list[ListingCandidate] = []
        pattern = re.compile(r'<a[^>]+class="search-product-link"[^>]+href="([^"]+)"[^>]*>.*?<div[^>]+class="name"[^>]*>(.*?)</div>', re.S)
        for rank, m in enumerate(pattern.finditer(html), start=1):
            if rank > self.max_candidates:
                break
            href = m.group(1)
            title = _strip_html(m.group(2))
            full_url = f"https://www.coupang.com{href}" if href.startswith("/") else href
            item_id = re.sub(r"\W+", "_", href)[-30:] or f"cp_{rank}"
            candidates.append(ListingCandidate(platform=self.source_name, item_id=item_id, url=full_url, title=title, source_rank=rank, source_query=query_hint, extracted_evidence="search_html"))
        return candidates

    async def enrich_listing(self, context, listing_url: str) -> ListingMeta:
        text = await _fetch_page_text(context, listing_url, timeout_ms=self.timeout_ms)
        price = _to_num(_first_match(text, r"([0-9,]+)\s*원"))
        rating = _to_num(_first_match(text, r"평점\s*([0-9.]+)"))
        review = _to_num(_first_match(text, r"리뷰\s*([0-9,]+)"))
        return ListingMeta(price_min=price, price_max=price, rating=rating, review_count=int(review) if review else None, views_estimated=review)


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _first_match(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _to_num(text: str | None) -> float | None:
    if not text:
        return None
    s = re.sub(r"[^0-9.]", "", text)
    try:
        return float(s)
    except ValueError:
        return None


async def _fetch_page_text(context, url: str, timeout_ms: int) -> str:
    if context is not None:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        html = await page.content()
        await page.close()
        return _strip_html(html)

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as resp:
        return _strip_html(resp.read().decode("utf-8", errors="ignore"))
