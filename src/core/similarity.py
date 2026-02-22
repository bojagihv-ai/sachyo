from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import hashlib

from src.core.models import SimilarityResult


def _read_bytes(path: str | Path) -> bytes | None:
    try:
        return Path(path).read_bytes()
    except Exception:  # noqa: BLE001
        return None


def _byte_digest_distance(a: bytes, b: bytes) -> int:
    ha = hashlib.sha1(a).hexdigest()
    hb = hashlib.sha1(b).hexdigest()
    return sum(x != y for x, y in zip(ha, hb))


def _size_similarity(a: bytes, b: bytes) -> float:
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    return min(la, lb) / max(la, lb)


def token_jaccard(a: str, b: str) -> float:
    sa = set(x.lower() for x in a.split() if x.strip())
    sb = set(x.lower() for x in b.split() if x.strip())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compare_images(source_image_path: str, candidate_image_path: str, title_a: str = "", title_b: str = "", query_hint: str | None = None) -> SimilarityResult:
    a = _read_bytes(source_image_path)
    b = _read_bytes(candidate_image_path)
    if a is None or b is None:
        return SimilarityResult(reason="image_load_failed")

    digest_dist = _byte_digest_distance(a, b)
    size_sim = _size_similarity(a, b)
    exact = 1.0 if a == b else 0.0

    result = SimilarityResult(
        phash_distance=digest_dist,
        dhash_distance=digest_dist,
        ssim=exact if exact == 1.0 else size_sim,
        embedding_similarity=max(size_sim, exact),
        color_similarity=size_sim,
        text_similarity=token_jaccard(f"{title_a} {query_hint or ''}", title_b),
    )
    return classify_similarity(result)


def classify_similarity(result: SimilarityResult) -> SimilarityResult:
    T1, S1, E1 = 8, 0.92, 0.95
    E2, C2 = 0.88, 0.7
    E3 = 0.75
    reason = []
    if result.phash_distance is not None and result.phash_distance <= T1 and ((result.ssim or 0) >= S1 or (result.embedding_similarity or 0) >= E1):
        result.class_label = "class_1_same_photo"
        score = 90 + (1 - min(result.phash_distance / max(T1, 1), 1)) * 10
        reason.append("digest/size high match")
    elif (result.embedding_similarity or 0) >= E2 and (result.color_similarity or 0) >= C2:
        result.class_label = "class_2_same_product_diff_photo"
        score = 75 + (result.embedding_similarity or 0) * 15
        reason.append("size/color matched")
    elif (result.embedding_similarity or 0) >= E3 and result.text_similarity >= 0.35:
        result.class_label = "class_3_inferred_same_product"
        score = 55 + (result.embedding_similarity or 0) * 20 + result.text_similarity * 10
        reason.append("text/model hint supported")
    else:
        result.class_label = "not_same_product"
        score = 20 + max((result.embedding_similarity or 0), 0) * 20
        reason.append("weak evidence")
    score += result.text_similarity * 5
    result.score = max(0.0, min(100.0, round(score, 2)))
    result.reason = "; ".join(reason)
    return result


def similarity_to_dict(sim: SimilarityResult) -> dict:
    return asdict(sim)
