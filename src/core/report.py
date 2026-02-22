from __future__ import annotations

import csv
import json
from pathlib import Path

from src.core.models import CandidateRecord


def _to_rows(records: list[CandidateRecord]) -> list[dict]:
    rows = []
    for r in records:
        rows.append(
            {
                "platform": r.candidate.platform,
                "item_id": r.candidate.item_id,
                "url": r.candidate.url,
                "title": r.candidate.title,
                "seller": r.candidate.seller,
                "image_url": r.candidate.image_url,
                "source_rank": r.candidate.source_rank,
                "price_min": r.meta.price_min,
                "price_max": r.meta.price_max,
                "shipping_fee": r.meta.shipping_fee,
                "rating": r.meta.rating,
                "review_count": r.meta.review_count,
                "sales_index": r.meta.sales_index,
                "views_estimated": r.meta.views_estimated,
                "class_label": r.similarity.class_label,
                "score": r.similarity.score,
                "reason": r.similarity.reason,
                "verified_flag": r.verification.verified_flag,
                "confidence": r.verification.confidence,
                "fail_reasons": " | ".join(r.verification.fail_reasons),
                "compare_summary": r.verification.compare_summary,
                "checklist_json": json.dumps(r.verification.checklist, ensure_ascii=False),
                "detail_image_count": len(r.download.downloaded_files),
                "detail_image_fail_count": len(r.download.failed_urls),
                "detail_image_urls_json": json.dumps(r.download.extracted_urls, ensure_ascii=False),
            }
        )
    return rows


def _sort_rows(rows: list[dict], key: str, reverse: bool = False, topn: int = 20) -> list[dict]:
    def cast(v):
        try:
            return float(v)
        except Exception:  # noqa: BLE001
            return -1e18 if reverse else 1e18

    return sorted(rows, key=lambda r: cast(r.get(key)), reverse=reverse)[:topn]


def _build_leaderboards(rows: list[dict]) -> list[dict]:
    boards: list[dict] = []
    for r in _sort_rows(rows, "price_min", reverse=False):
        boards.append({"board": "lowest_price", **r})
    for r in _sort_rows(rows, "review_count", reverse=True):
        boards.append({"board": "most_reviews", **r})
    for r in _sort_rows(rows, "sales_index", reverse=True):
        boards.append({"board": "top_sales_index", **r})
    overall_rows = []
    for r in rows:
        conf = float(r.get("confidence") or 0)
        score = float(r.get("score") or 0)
        rr = dict(r)
        rr["overall_rank_score"] = conf * 70 + score * 0.3
        overall_rows.append(rr)
    for r in _sort_rows(overall_rows, "overall_rank_score", reverse=True):
        boards.append({"board": "overall", **r})
    return boards


def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_reports(records: list[CandidateRecord], report_dir: Path, create_xlsx: bool = False) -> dict[str, Path]:
    rows = _to_rows(records)
    verified_rows = [r for r in rows if r.get("verified_flag") is True]
    leader_rows = _build_leaderboards(rows)

    paths = {
        "candidates": report_dir / "candidates.csv",
        "verified": report_dir / "verified.csv",
        "leaderboards": report_dir / "leaderboards.csv",
    }
    _write_csv(paths["candidates"], rows)
    _write_csv(paths["verified"], verified_rows)
    _write_csv(paths["leaderboards"], leader_rows)

    if create_xlsx:
        # Optional feature requires pandas/openpyxl; write a notice file in dependency-limited env.
        notice = report_dir / "report.xlsx.txt"
        notice.write_text("XLSX generation skipped: pandas/openpyxl not available in this environment.", encoding="utf-8")
        paths["xlsx_notice"] = notice

    return paths


def write_manual_review_html(records: list[CandidateRecord], report_path: Path, topn: int = 30) -> Path:
    selected = sorted(records, key=lambda r: (r.verification.confidence, r.similarity.score), reverse=True)[:topn]
    rows = []
    for i, r in enumerate(selected):
        rows.append(
            f"""
            <tr>
              <td><input type='checkbox' data-key='{r.candidate.platform}:{r.candidate.item_id}' /></td>
              <td>{i+1}</td>
              <td><img src='{r.candidate.image_url or ''}' style='max-width:120px;max-height:120px;'/></td>
              <td>{r.candidate.title}</td>
              <td>{r.candidate.platform}</td>
              <td>{r.meta.price_min}</td>
              <td>{r.verification.confidence}</td>
              <td><a href='{r.candidate.url}' target='_blank'>link</a></td>
            </tr>
            """
        )

    html = f"""
    <html><body>
    <h2>Manual Verification Report</h2>
    <p>Check rows and run an external script to merge with verified.csv if needed.</p>
    <table border='1' cellspacing='0' cellpadding='4'>
      <tr><th>same?</th><th>#</th><th>thumb</th><th>title</th><th>platform</th><th>price</th><th>conf</th><th>url</th></tr>
      {''.join(rows)}
    </table>
    </body></html>
    """
    report_path.write_text(html, encoding="utf-8")
    return report_path
