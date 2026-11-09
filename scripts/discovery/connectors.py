"""HTTP and format connectors for the Genomic Atlas discovery engine.

Only source URLs explicitly listed in the registry are fetched. The crawler does
not recursively spider the web and does not store full third-party page bodies.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlsplit,
    urlunsplit,
)
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen
import hashlib
import re
import unicodedata
import xml.etree.ElementTree as ET


USER_AGENT = (
    "GenomicAtlasBot/0.1 "
    "(+https://github.com/gitsselcc/genomic-atlas)"
)
MAX_RESPONSE_BYTES = 3_000_000
TRACKING_PARAMETERS = {
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref_src",
}


@dataclass
class FetchResult:
    url: str
    status: int
    headers: dict[str, str]
    content: bytes


def is_http_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        return (
            parsed.scheme.lower() in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def canonicalize_url(url: str, base_url: str | None = None) -> str:
    """Resolve and normalize a URL without discarding meaningful query data."""
    absolute = urljoin(base_url, url) if base_url else url
    if not is_http_url(absolute):
        raise ValueError(f"URL HTTP(S) no válida: {absolute}")

    parsed = urlsplit(absolute)
    host = (parsed.hostname or "").lower()
    port = parsed.port
    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        host = f"{host}:{port}"

    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMETERS
    ]
    query.sort()
    path = parsed.path or "/"
    return urlunsplit((
        parsed.scheme.lower(),
        host,
        path,
        urlencode(query, doseq=True),
        "",
    ))


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value).strip().lower()


def keyword_match(value: str, keywords: list[str] | None) -> bool:
    if not keywords:
        return True
    normalized = normalize_text(value)
    return any(
        normalize_text(keyword) in normalized
        for keyword in keywords
        if isinstance(keyword, str) and keyword.strip()
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def decode_response(content: bytes, headers: dict[str, str]) -> str:
    content_type = next(
        (value for key, value in headers.items() if key.lower() == "content-type"),
        "",
    )
    match = re.search(r"charset\s*=\s*['\"]?([^;'\"]+)", content_type, re.I)
    encoding = match.group(1).strip() if match else "utf-8"
    try:
        return content.decode(encoding, errors="replace")
    except LookupError:
        return content.decode("utf-8", errors="replace")


def fetch_url(
    url: str,
    timeout: int = 20,
    headers: dict[str, str] | None = None,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> FetchResult:
    """Fetch one configured URL; return HTTP errors as results for inspection."""
    if not is_http_url(url):
        raise ValueError(f"Solo se permiten URLs HTTP(S): {url}")

    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xml,application/rss+xml,"
            "application/atom+xml,text/xml,*/*;q=0.5"
        ),
    }
    if headers:
        request_headers.update(headers)

    request = Request(url, headers=request_headers)
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as exc:
        body = exc.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(f"Respuesta demasiado grande: {url}")
        return FetchResult(
            url=exc.geturl(),
            status=exc.code,
            headers=dict(exc.headers.items()),
            content=body,
        )
    except URLError as exc:
        raise RuntimeError(f"No se pudo consultar {url}: {exc.reason}") from exc

    with response:
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(
                f"Respuesta superior al límite de {max_bytes} bytes: {url}"
            )
        return FetchResult(
            url=response.geturl(),
            status=getattr(response, "status", 200),
            headers=dict(response.headers.items()),
            content=body,
        )


def robots_allowed(
    url: str,
    cache: dict[str, tuple[bool, str]],
    timeout: int = 20,
) -> tuple[bool, str]:
    """Respect robots.txt; fail closed when its policy cannot be checked."""
    parsed = urlsplit(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin in cache:
        return cache[origin]

    robots_url = f"{origin}/robots.txt"
    try:
        result = fetch_url(robots_url, timeout=timeout, max_bytes=500_000)
    except Exception as exc:  # network uncertainty: do not crawl the domain
        decision = (False, f"No se pudo comprobar robots.txt: {exc}")
        cache[origin] = decision
        return decision

    if result.status in {404, 410}:
        decision = (True, "robots.txt no existe")
    elif result.status < 200 or result.status >= 300:
        decision = (False, f"robots.txt respondió HTTP {result.status}")
    else:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(decode_response(result.content, result.headers).splitlines())
        allowed = parser.can_fetch(USER_AGENT, url)
        decision = (
            allowed,
            "permitido por robots.txt" if allowed else "bloqueado por robots.txt",
        )

    cache[origin] = decision
    return decision


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _clean_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_datetime(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def parse_feed(content: bytes, base_url: str) -> list[dict]:
    """Parse RSS 2.0 or Atom entries using the Python standard library."""
    root = ET.fromstring(content)
    entries = [
        element for element in root.iter()
        if _local_name(element.tag) in {"item", "entry"}
    ]
    output = []

    for entry in entries:
        fields: dict[str, str] = {}
        link = ""
        for child in list(entry):
            name = _local_name(child.tag)
            value = "".join(child.itertext()).strip()
            if name == "link":
                rel = child.attrib.get("rel", "alternate").lower()
                candidate_link = child.attrib.get("href") or value
                if candidate_link and (rel == "alternate" or not link):
                    link = candidate_link
            elif name in {
                "title", "description", "summary", "content",
                "pubdate", "published", "updated", "date", "guid", "id",
            }:
                fields[name] = value

        link = link or fields.get("guid") or fields.get("id", "")
        if not link or not is_http_url(urljoin(base_url, link)):
            continue

        title = _clean_markup(fields.get("title", "")) or link
        summary = _clean_markup(
            fields.get("summary")
            or fields.get("description")
            or fields.get("content")
            or ""
        )
        published = (
            fields.get("published")
            or fields.get("pubdate")
            or fields.get("updated")
            or fields.get("date")
        )
        output.append({
            "title": title,
            "url": canonicalize_url(link, base_url),
            "summary": summary[:700],
            "published_at": parse_datetime(published),
        })

    return output


def parse_sitemap_document(content: bytes) -> dict[str, list[dict[str, str]]]:
    """Parse a sitemap URL set or return child sitemap URLs from an index."""
    root = ET.fromstring(content)
    root_name = _local_name(root.tag)
    result: dict[str, list[dict[str, str]]] = {"urls": [], "sitemaps": []}

    if root_name == "sitemapindex":
        for node in root:
            if _local_name(node.tag) != "sitemap":
                continue
            loc = next(
                (child.text.strip() for child in node
                 if _local_name(child.tag) == "loc" and child.text),
                "",
            )
            if loc and is_http_url(loc):
                result["sitemaps"].append({"url": canonicalize_url(loc)})
        return result

    for node in root:
        if _local_name(node.tag) != "url":
            continue
        values = {
            _local_name(child.tag): (child.text or "").strip()
            for child in node
        }
        loc = values.get("loc", "")
        if loc and is_http_url(loc):
            result["urls"].append({
                "url": canonicalize_url(loc),
                "lastmod": values.get("lastmod", ""),
            })

    return result


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.description = ""
        self.canonical = ""
        self.links: list[dict[str, str]] = []
        self.in_title = False
        self.current_href: str | None = None
        self.current_anchor: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        tag = tag.lower()

        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = (
                attributes.get("name")
                or attributes.get("property")
                or ""
            ).lower()
            if key in {"description", "og:description"} and not self.description:
                self.description = attributes.get("content", "").strip()
        elif tag == "link":
            rel = attributes.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonical = attributes.get("href", "").strip()
        elif tag == "a" and attributes.get("href"):
            self.current_href = attributes["href"].strip()
            self.current_anchor = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.current_href is not None:
            self.current_anchor.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "a" and self.current_href is not None:
            label = re.sub(r"\s+", " ", " ".join(self.current_anchor)).strip()
            self.links.append({"href": self.current_href, "text": label})
            self.current_href = None
            self.current_anchor = []


def parse_html_document(content: bytes, headers: dict[str, str]) -> dict:
    parser = _PageParser()
    parser.feed(decode_response(content, headers))
    return {
        "title": re.sub(r"\s+", " ", " ".join(parser.title_parts)).strip(),
        "description": parser.description[:700],
        "canonical": parser.canonical,
        "links": parser.links,
    }
