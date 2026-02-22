from __future__ import annotations

import asyncio
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from src.core.models import DownloadResult, ListingCandidate, ListingMeta

try:
    from playwright.async_api import Page
except ModuleNotFoundError:  # pragma: no cover
    Page = object


class RateLimiter:
    def __init__(self, min_interval_s: float = 1.0):
        self.min_interval_s = min_interval_s
        self._last = 0.0

    async def wait(self):
        gap = time.time() - self._last
        if gap < self.min_interval_s:
            await asyncio.sleep(self.min_interval_s - gap)
        self._last = time.time()


class BaseAdapter(ABC):
    source_name = "base"
    needs_browser = True

    def __init__(self, max_candidates: int = 30, timeout_ms: int = 15000):
        self.max_candidates = max_candidates
        self.timeout_ms = timeout_ms
        self.rate_limiter = RateLimiter(1.0)

    @abstractmethod
    async def search_by_image(self, context, image_path: str, query_hint: str | None) -> list[ListingCandidate]:
        ...

    @abstractmethod
    async def enrich_listing(self, context, listing_url: str) -> ListingMeta:
        ...

    async def crawl_detail_images(self, context, listing_url: str, save_dir: Path, save_snapshot: bool = True) -> DownloadResult:
        if context is None:
            return DownloadResult(failed_urls=["playwright_not_available"])

        await self.rate_limiter.wait()
        page = await context.new_page()
        await page.goto(listing_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        await auto_scroll(page)
        image_urls = await extract_image_urls(page, listing_url)

        result = DownloadResult(extracted_urls=image_urls)
        if save_snapshot:
            html_path = save_dir / "page_snapshot.html"
            html_path.write_text(await page.content(), encoding="utf-8")
            result.page_snapshot_html = str(html_path)
            png_path = save_dir / "page_full.png"
            await page.screenshot(path=str(png_path), full_page=True)
            result.page_full_png = str(png_path)

        for idx, img_url in enumerate(image_urls):
            suffix = Path(urlparse(img_url).path).suffix or ".jpg"
            out = save_dir / f"detail_{idx:04d}{suffix}"
            ok = download_with_retry(img_url, out, referer=listing_url)
            if ok:
                result.downloaded_files.append(str(out))
            else:
                result.failed_urls.append(img_url)

        await page.close()
        return result


def download_with_retry(url: str, out_path: Path, referer: str | None = None) -> bool:
    headers = {"User-Agent": "Mozilla/5.0"}
    if referer:
        headers["Referer"] = referer

    for i in range(3):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as resp:
                content = resp.read()
                if content:
                    out_path.write_bytes(content)
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(0.5 * (2**i))
    return False


async def auto_scroll(page: Page, rounds: int = 8):
    for _ in range(rounds):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(350)


async def extract_image_urls(page: Page, base_url: str) -> list[str]:
    js = """
    () => {
      const urls = new Set();
      const add = (u) => {
        if (!u) return;
        const parts = String(u).split(',').map(x => x.trim().split(' ')[0]);
        for (const p of parts) {
          if (p && !p.startsWith('data:')) urls.add(p);
        }
      };
      document.querySelectorAll('img').forEach(img => {
        add(img.src); add(img.getAttribute('data-src')); add(img.getAttribute('data-original')); add(img.srcset);
      });
      document.querySelectorAll('*').forEach(el => {
        const bg = getComputedStyle(el).backgroundImage;
        if (bg && bg.includes('url(')) {
          const m = bg.match(/url\(["']?(.*?)["']?\)/);
          if (m && m[1]) add(m[1]);
        }
      });
      document.querySelectorAll('script').forEach(s => { if (s.textContent) urls.add(s.textContent); });
      return Array.from(urls);
    }
    """
    raw = await page.evaluate(js)

    urls = set()
    pattern = re.compile(r"https?://[^\s\"'<>]+(?:jpg|jpeg|png|webp|gif)", re.IGNORECASE)
    for item in raw:
        if item.startswith("http"):
            urls.add(item)
        elif "{" in item or "[" in item:
            for m in pattern.findall(item):
                urls.add(m)
        else:
            joined = urljoin(base_url, item)
            if joined.startswith("http"):
                urls.add(joined)

    normalized = []
    seen = set()
    for u in urls:
        nu = u.split("?")[0]
        if nu not in seen:
            normalized.append(u)
            seen.add(nu)
    return normalized
