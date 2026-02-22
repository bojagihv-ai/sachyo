from __future__ import annotations

import re
from dataclasses import asdict

from src.core.models import ListingCandidate, ListingMeta, SimilarityResult, VerificationResult


def _extract_specs(text: str) -> set[str]:
    patterns = [r"\d+\s?(?:ml|g|kg|cm|mm|m|ea|개|입)", r"\d+x\d+"]
    found: set[str] = set()
    lower = text.lower()
    for p in patterns:
        found.update(re.findall(p, lower))
    return found


def verify_candidate(
    src_title: str,
    candidate: ListingCandidate,
    meta: ListingMeta,
    sim: SimilarityResult,
) -> VerificationResult:
    checklist = {}
    fail_reasons: list[str] = []

    def put(k: str, passed: bool, confidence: float, note: str):
        checklist[k] = {"pass": passed, "confidence": confidence, "note": note}
        if not passed:
            fail_reasons.append(f"{k}:{note}")

    put("1_image_similarity", sim.score >= 65, min(1.0, sim.score / 100), sim.class_label)

    source_tokens = set(src_title.lower().split())
    cand_tokens = set(candidate.title.lower().split())
    core_overlap = len(source_tokens & cand_tokens)
    put("2_title_tokens", core_overlap >= 2, min(1.0, core_overlap / 5), f"overlap={core_overlap}")

    spec_src = _extract_specs(src_title)
    spec_cand = _extract_specs(candidate.title)
    spec_overlap = len(spec_src & spec_cand)
    put("3_specs", spec_overlap > 0 or not spec_src, min(1.0, spec_overlap), f"spec_overlap={spec_overlap}")

    material_keywords = ["cotton", "steel", "플라스틱", "실리콘", "가죽", "wood", "metal"]
    mat_src = {k for k in material_keywords if k in src_title.lower()}
    mat_cand = {k for k in material_keywords if k in candidate.title.lower()}
    put("4_material", mat_src == mat_cand or not mat_src, 0.8 if mat_src == mat_cand else 0.4, "material compare")

    qty_words = ["set", "세트", "1개", "2개", "10개", "pack", "입"]
    qty_src = [x for x in qty_words if x in src_title.lower()]
    qty_cand = [x for x in qty_words if x in candidate.title.lower()]
    put("5_set_quantity", qty_src == qty_cand or not qty_src, 0.75 if qty_src == qty_cand else 0.4, "qty compare")

    put("6_color_options", True, 0.6, "option-level color needs manual review")
    put("7_ocr_label", True, 0.5, "ocr optional")

    if meta.price_min and meta.price_min > 0:
        # Heuristic: no source price baseline known, just flag absurd values.
        price_warning = meta.price_min > 1_000_000
        put("8_price_anomaly", not price_warning, 0.8 if not price_warning else 0.2, f"price={meta.price_min}")
    else:
        put("8_price_anomaly", True, 0.5, "price not available")

    put("9_review_mentions", True, 0.5, "review NLP optional")
    put("10_category_match", bool(meta.category), 0.7 if meta.category else 0.3, f"category={meta.category}")

    avg_conf = sum(x["confidence"] for x in checklist.values()) / len(checklist)
    required_fail = [k for k, v in checklist.items() if not v["pass"] and k in {"1_image_similarity", "2_title_tokens"}]
    verified = avg_conf >= 0.62 and not required_fail and sim.class_label != "not_same_product"

    return VerificationResult(
        verified_flag=verified,
        confidence=round(avg_conf, 3),
        fail_reasons=fail_reasons,
        compare_summary=f"sim={sim.class_label}, score={sim.score}, avg_conf={avg_conf:.2f}",
        checklist=checklist,
    )


def verification_to_dict(verification: VerificationResult) -> dict:
    return asdict(verification)
