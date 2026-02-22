from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunConfig:
    image: str
    query_hint: str | None = None
    max_candidates_per_source: int = 30
    topk_final: int = 50
    sources: list[str] = field(default_factory=lambda: ["coupang", "naver"])
    output_dir: str = "./output"
    create_xlsx: bool = False
    save_snapshots: bool = True
    manual_review_topn: int = 30


@dataclass
class ListingCandidate:
    platform: str
    item_id: str
    url: str
    title: str
    seller: str | None = None
    image_url: str | None = None
    source_rank: int = 9999
    source_query: str | None = None
    extracted_evidence: str | None = None


@dataclass
class ListingMeta:
    price_min: float | None = None
    price_max: float | None = None
    shipping_fee: float | None = None
    rocket_or_fast_shipping: str | None = None
    rating: float | None = None
    review_count: int | None = None
    sales_index: float | None = None
    views_estimated: float | None = None
    options: list[dict[str, Any]] = field(default_factory=list)
    category: str | None = None


@dataclass
class SimilarityResult:
    phash_distance: int | None = None
    dhash_distance: int | None = None
    ssim: float | None = None
    embedding_similarity: float | None = None
    color_similarity: float | None = None
    text_similarity: float = 0.0
    score: float = 0.0
    class_label: str = "unclassified"
    reason: str = ""


@dataclass
class VerificationResult:
    verified_flag: bool
    confidence: float
    fail_reasons: list[str]
    compare_summary: str
    checklist: dict[str, dict[str, Any]]


@dataclass
class DownloadResult:
    extracted_urls: list[str] = field(default_factory=list)
    downloaded_files: list[str] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)
    page_snapshot_html: str | None = None
    page_full_png: str | None = None


@dataclass
class CandidateRecord:
    candidate: ListingCandidate
    meta: ListingMeta
    similarity: SimilarityResult
    verification: VerificationResult
    download: DownloadResult
