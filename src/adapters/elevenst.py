from __future__ import annotations

import re
from urllib.parse import quote

from src.adapters.base import BaseAdapter
from src.adapters.coupang import _fetch_page_text, _first_match, _strip_html, _to_num
from src.core.models import ListingCandidate, ListingMeta


class ElevenStAdapter(BaseAdapter):
    source_name = "11st"

    async def search_by_image(self, context, image_path: str, query_hint: str | None) -> list[ListingCandidate]:
        if not query_hint or context is None:
            return []

        page = await context.new_page()
        url = f"https://search.11st.co.kr/Search.tmall?kwd={quote(query_hint)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        await page.wait_for_timeout(1200)
        html = await page.content()
        await page.close()

        candidates = []
        # 11번가 마크업 변경에 대비해 다중 패턴 사용
        patterns = [
            re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S),
        ]

        rank = 0
        for pat in patterns:
            for m in pat.finditer(html):
                href = m.group(1)
                text = _strip_html(m.group(2))
                if not href.startswith("http"):
                    continue
                if len(text) < 6:
                    continue
                if "11st.co.kr/products/" not in href:
                    continue
                rank += 1
                if rank > self.max_candidates:
                    break
                item_id = re.sub(r"\W+", "_", href)[-30:] or f"11st_{rank}"
                candidates.append(
                    ListingCandidate(
                        platform=self.source_name,
                        item_id=item_id,
                        url=href,
                        title=text,
                        source_rank=rank,
                        source_query=query_hint,
                        extracted_evidence="search_html",
                    )
                )
            if candidates:
                break

        return candidates

    async def enrich_listing(self, context, listing_url: str) -> ListingMeta:
        text = await _fetch_page_text(context, listing_url, timeout_ms=self.timeout_ms)
        price = _to_num(_first_match(text, r"([0-9,]+)\s*원"))
        rating = _to_num(_first_match(text, r"평점\s*([0-9.]+)"))
        review = _to_num(_first_match(text, r"리뷰\s*([0-9,]+)"))
        return ListingMeta(
            price_min=price,
            price_max=price,
            rating=rating,
            review_count=int(review) if review else None,
            views_estimated=review,
        )
