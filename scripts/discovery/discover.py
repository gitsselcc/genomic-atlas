"""Discover candidate pages from explicitly registered sources."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from connectors import (  # noqa: E402
    canonicalize_url,
    fetch_url,
    keyword_match,
    parse_feed,
    parse_html_document,
    parse_sitemap_document,
    robots_allowed,
    sha256_text,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def load_registry(path: Path) -> list[dict]:
    """Load JSON-compatible YAML without requiring PyYAML."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "El registro debe ser JSON válido (también compatible con YAML)"
        ) from exc

    if not isinstance(raw, list):
        raise ValueError("El registro debe ser una lista")

    seen = set()
    for index, source in enumerate(raw):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            raise ValueError(f"{label}: debe ser objeto")

        for field in ("source_id", "name", "url", "source_type"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"{label}.{field}: obligatorio")

        source_id = source["source_id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", source_id):
            raise ValueError(f"{label}.source_id inválido")
        if source_id in seen:
            raise ValueError(f"{label}.source_id duplicado")
        seen.add(source_id)

        if source["source_type"] not in {"rss", "sitemap", "webpage"}:
            raise ValueError(f"{label}.source_type no admitido")
        canonicalize_url(source["url"])

        if not isinstance(source.get("active", True), bool):
            raise ValueError(f"{label}.active debe ser booleano")
        if not isinstance(source.get("areas", ["all"]), list):
            raise ValueError(f"{label}.areas debe ser una lista")
        if not isinstance(source.get("keywords", []), list):
            raise ValueError(f"{label}.keywords debe ser una lista")

    return raw


def _fetch(url: str, source: dict, robots_cache: dict):
    """Check robots.txt before requesting a source or discovered sitemap."""
    allowed, reason = robots_allowed(
        url,
        robots_cache,
        timeout=source.get("robots_timeout", 8),
    )
    if not allowed:
        raise PermissionError(reason)

    response = fetch_url(
        url,
        timeout=source.get("timeout", 20),
        headers=source.get("headers", {}),
        max_bytes=source.get("max_response_bytes", 3_000_000),
    )
    if not 200 <= response.status < 300:
        raise RuntimeError(f"HTTP {response.status}: {url}")

    return response.content, response.headers


def collect_source(source: dict, robots_cache: dict) -> list[dict]:
    """Collect candidates from one configured RSS, sitemap or HTML source."""
    content, headers = _fetch(source["url"], source, robots_cache)
    source_type = source["source_type"]

    if source_type == "rss":
        items = parse_feed(content, source["url"])

    elif source_type == "sitemap":
        parsed = parse_sitemap_document(content)
        pages = parsed["urls"]

        for child in parsed["sitemaps"][: source.get("max_child_sitemaps", 10)]:
            child_content, _ = _fetch(child["url"], source, robots_cache)
            pages.extend(parse_sitemap_document(child_content)["urls"])

        items = [
            {
                "url": page["url"],
                "title": page["url"],
                "summary": "",
                "lastmod": page.get("lastmod"),
            }
            for page in pages[: source.get("max_pages", 300)]
        ]

    else:
        page = parse_html_document(content, headers)
        base_url = page["canonical"] or source["url"]
        items = []

        for link in page["links"]:
            href = link.get("href", "")
            if not href or href.startswith(
                ("#", "mailto:", "tel:", "javascript:")
            ):
                continue

            url = canonicalize_url(href, base_url)
            source_host = urlsplit(source["url"]).hostname
            target_host = urlsplit(url).hostname
            if (
                target_host != source_host
                and not source.get("allow_external_links", False)
            ):
                continue

            items.append({
                "url": url,
                "title": link.get("text") or url,
                "summary": page["description"],
            })

        if not items:
            items = [{
                "url": base_url,
                "title": page["title"] or source["name"],
                "summary": page["description"],
            }]

    candidates = []
    detected_at = utc_now()

    for item in items:
        searchable_text = " ".join((
            item.get("title", ""),
            item.get("summary", ""),
            item.get("url", ""),
        ))
        if not keyword_match(searchable_text, source.get("keywords", [])):
            continue

        url = canonicalize_url(item["url"], source["url"])
        title = (item.get("title") or url).strip()
        summary = (item.get("summary") or "").strip()

        candidates.append({
            "candidate_id": sha256_text(url)[:20],
            "source_id": source["source_id"],
            "source_name": source["name"],
            "source_url": source["url"],
            "title": title[:300],
            "url": url,
            "summary": summary[:700],
            "published_at": item.get("published_at"),
            "source_lastmod": item.get("lastmod") or None,
            "detected_at": detected_at,
            "content_hash": sha256_text(title + "\n" + summary),
            "areas": source.get("areas", ["all"]),
            "status": "pending_review",
        })

    return candidates


def merge_candidates(path: Path, incoming: list[dict]) -> tuple[int, int]:
    """Append new URLs and changed content; skip unchanged candidates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    known = {}

    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                known[row["url"]] = row.get("content_hash", "")
            except (json.JSONDecodeError, KeyError):
                continue

    added = 0
    changed = 0

    with path.open("a", encoding="utf-8") as handle:
        for row in incoming:
            previous_hash = known.get(row["url"])
            if previous_hash == row["content_hash"]:
                continue

            if previous_hash is None:
                added += 1
            else:
                changed += 1
                row["change_detected"] = True

            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            known[row["url"]] = row["content_hash"]

    return added, changed


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genomic Atlas source discovery"
    )
    parser.add_argument(
        "--registry",
        default="research/sources/registry.json",
        help="Registro de fuentes",
    )
    parser.add_argument(
        "--output",
        default="research/discovery/candidates.jsonl",
        help="Archivo JSONL de candidatos",
    )
    parser.add_argument(
        "--report",
        default="research/discovery/run_report.json",
        help="Reporte JSON de la ejecución",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Devuelve error si falla cualquier fuente",
    )
    args = parser.parse_args()

    try:
        sources = load_registry(ROOT / args.registry)
    except (OSError, ValueError) as exc:
        print(f"ERROR en registro: {exc}", file=sys.stderr)
        return 1

    active_sources = [
        source for source in sources if source.get("active", True)
    ]
    if not active_sources:
        print("ERROR: no hay fuentes activas en el registro", file=sys.stderr)
        return 1

    started_at = utc_now()
    robots_cache = {}
    discovered = []
    successful_sources = []
    failed_sources = []

    print(
        f"Fuentes registradas: {len(sources)} | "
        f"activas: {len(active_sources)}"
    )

    for source in active_sources:
        try:
            candidates = collect_source(source, robots_cache)
            discovered.extend(candidates)
            successful_sources.append({
                "source_id": source["source_id"],
                "candidate_count": len(candidates),
            })
            print(
                f"OK  {source['source_id']}: "
                f"{len(candidates)} candidatos"
            )
        except Exception as exc:
            message = str(exc).replace("\n", " ")[:1000]
            failed_sources.append({
                "source_id": source["source_id"],
                "error": message,
            })
            print(
                f"::warning title=Source unavailable::{source['source_id']}: "
                f"{message}",
                file=sys.stderr,
            )

    # De-duplicate by canonical URL within this run, keeping first provenance.
    unique = {}
    for candidate in discovered:
        unique.setdefault(candidate["url"], candidate)

    output_path = ROOT / args.output
    added, changed = merge_candidates(output_path, list(unique.values()))

    if failed_sources and successful_sources:
        status = "partial_success"
    elif failed_sources:
        status = "failed"
    else:
        status = "success"

    report = {
        "status": status,
        "started_at": started_at,
        "completed_at": utc_now(),
        "registered_sources": len(sources),
        "active_sources": len(active_sources),
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
        "unique_candidates_this_run": len(unique),
        "new_candidates": added,
        "changed_candidates": changed,
        "candidate_file": args.output,
    }
    write_report(ROOT / args.report, report)

    print(
        f"Resultado: {len(unique)} únicos | {added} nuevos | "
        f"{changed} cambios | {len(failed_sources)} fuentes con error"
    )
    print(f"Estado: {status}")
    print(f"Candidatos: {args.output}")
    print(f"Reporte: {args.report}")

    # A partial run is useful and should preserve its cache/history. Fail only
    # when every active source failed, or when the caller explicitly requests
    # strict mode.
    if not successful_sources:
        return 1
    if args.strict and failed_sources:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
