#!/usr/bin/env python3
import json
import re
import sys
import time
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://help.splunk.com"
SEED_URLS = [
    "https://help.splunk.com/en/splunk-cloud-platform/search/spl2-overview/what-is-spl2",
    "https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-reference/introduction/introduction",
    "https://help.splunk.com/en/splunk-cloud-platform/search/spl2-search-manual/getting-started/quick-start-write-and-run-a-basic-spl2-search/start-searching-data-using-spl2",
]
ALLOWED_PREFIXES = (
    "/en/splunk-cloud-platform/search/spl2-overview",
    "/en/splunk-cloud-platform/search/spl2-search-reference",
    "/en/splunk-cloud-platform/search/spl2-search-manual",
)
OUTPUT_ROOT = Path("research")
RAW_DIR = OUTPUT_ROOT / "raw"
EXTRACTED_DIR = OUTPUT_ROOT / "extracted"
INDEX_DIR = OUTPUT_ROOT / "index"
SESSION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; spl2-tutorial-bot/1.0; +https://help.splunk.com)",
}


@dataclass
class DocRecord:
    url: str
    title: str
    description: str
    last_modified_iso: str
    content_type: str
    section: str
    breadcrumbs: list[str]
    headings: list[dict]
    text: str
    related_links: list[dict]


def slugify_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    return "__".join(parts) + ".json"


def fetch(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def normalize_url(href: str) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
        return None
    absolute = urljoin(BASE_URL, href)
    parsed = urlparse(absolute)
    cleaned = parsed._replace(fragment="", query="").geturl()
    if any(parsed.path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return cleaned
    if cleaned.startswith("https://help.splunk.com/en/?resourceId="):
        return cleaned
    return None


def extract_urls(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    for tag in soup.find_all("a", href=True):
        normalized = normalize_url(tag["href"])
        if normalized:
            urls.add(normalized)
    return urls


def resource_ids_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article[role='article']")
    scope = str(article) if article is not None else html
    return sorted(set(re.findall(r"/en/\\?resourceId=([A-Za-z0-9_.-]+)", scope)))


def resolve_resource_id(session: requests.Session, resource_id: str) -> str | None:
    url = f"{BASE_URL}/en/?resourceId={resource_id}"
    response = session.get(url, allow_redirects=True, timeout=30)
    response.raise_for_status()
    final_url = response.url.split("#", 1)[0]
    parsed = urlparse(final_url)
    if any(parsed.path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return final_url
    return None


def markdownify(node) -> str:
    lines: list[str] = []
    for element in node.children:
        name = getattr(element, "name", None)
        if name is None:
            text = normalize_text(str(element))
            if text:
                lines.append(text)
            continue

        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(name[1])
            heading = normalize_text(element.get_text(" ", strip=True))
            if heading:
                lines.append(f'{"#" * level} {heading}')
            continue

        if name == "p":
            text = normalize_text(element.get_text(" ", strip=True))
            if text:
                lines.append(text)
            continue

        if name in {"div", "section", "article", "main"}:
            nested = markdownify(element)
            if nested:
                lines.extend(nested.splitlines())
            continue

        if name in {"ul", "ol"}:
            for li in element.find_all("li", recursive=False):
                text = normalize_text(li.get_text(" ", strip=True))
                if text:
                    lines.append(f"- {text}")
            continue

        if name == "pre":
            code = element.get_text("\n", strip=False).strip("\n")
            if code:
                lines.append("```")
                lines.append(code)
                lines.append("```")
            continue

        if name == "table":
            table_text = normalize_text(element.get_text(" | ", strip=True))
            if table_text:
                lines.append(table_text)
            continue

        if name == "figure":
            alt_text = normalize_text(element.get_text(" ", strip=True))
            if alt_text:
                lines.append(f"[Figure] {alt_text}")
            continue

        lines.extend(markdownify(element).splitlines())

    # Remove repeated adjacent lines caused by nested blocks.
    deduped: list[str] = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return "\n".join(deduped)


def normalize_text(value: str) -> str:
    value = unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\s+\n", "\n", value)
    return value.strip()


def parse_doc(url: str, html: str) -> DocRecord:
    soup = BeautifulSoup(html, "html.parser")
    title = normalize_text((soup.title.string if soup.title and soup.title.string else "").replace(" | Platform", ""))
    description = normalize_text((soup.find("meta", attrs={"name": "description"}) or {}).get("content", ""))
    last_modified_iso = (soup.find("meta", attrs={"name": "lastModifiedISO"}) or {}).get("content", "")
    content_type = (soup.find("meta", attrs={"name": "contentType"}) or {}).get("content", "")

    article = soup.select_one("article[role='article']")
    if article is None:
        raise ValueError(f"Could not find article content for {url}")

    breadcrumbs = [
        normalize_text(a.get_text(" ", strip=True))
        for a in soup.select("nav.breadcrumbs a")
        if normalize_text(a.get_text(" ", strip=True))
    ]
    headings = []
    for heading in article.select("h1, h2, h3, h4"):
        headings.append(
            {
                "level": heading.name,
                "id": heading.get("id", ""),
                "text": normalize_text(heading.get_text(" ", strip=True)),
            }
        )

    related_links = []
    for anchor in article.select("a[href]"):
        href = normalize_url(anchor["href"])
        text = normalize_text(anchor.get_text(" ", strip=True))
        if href and text:
            related_links.append({"text": text, "url": href})

    parsed = urlparse(url)
    section = parsed.path.split("/")[4] if len(parsed.path.split("/")) > 4 else "unknown"

    return DocRecord(
        url=url,
        title=title,
        description=description,
        last_modified_iso=last_modified_iso,
        content_type=content_type,
        section=section,
        breadcrumbs=breadcrumbs,
        headings=headings,
        text=markdownify(article),
        related_links=related_links,
    )


def write_doc(record: DocRecord) -> None:
    filename = slugify_url(record.url)
    payload = {
        "url": record.url,
        "title": record.title,
        "description": record.description,
        "last_modified_iso": record.last_modified_iso,
        "content_type": record.content_type,
        "section": record.section,
        "breadcrumbs": record.breadcrumbs,
        "headings": record.headings,
        "related_links": record.related_links,
        "text": record.text,
    }
    (EXTRACTED_DIR / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_raw(url: str, html: str) -> None:
    (RAW_DIR / slugify_url(url).replace(".json", ".html")).write_text(html, encoding="utf-8")


def summarize(records: Iterable[DocRecord]) -> None:
    records = list(records)
    manifest = [
        {
            "title": record.title,
            "url": record.url,
            "section": record.section,
            "content_type": record.content_type,
            "last_modified_iso": record.last_modified_iso,
            "headings": [heading["text"] for heading in record.headings],
        }
        for record in records
    ]
    (INDEX_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    section_counts: dict[str, int] = {}
    for record in records:
        section_counts[record.section] = section_counts.get(record.section, 0) + 1
    summary_lines = [
        "# SPL2 Corpus Summary",
        "",
        f"- Total documents: {len(records)}",
    ]
    for section, count in sorted(section_counts.items()):
        summary_lines.append(f"- {section}: {count}")
    (INDEX_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_ROOT.mkdir(exist_ok=True)
    RAW_DIR.mkdir(exist_ok=True)
    EXTRACTED_DIR.mkdir(exist_ok=True)
    INDEX_DIR.mkdir(exist_ok=True)

    session = requests.Session()
    session.headers.update(SESSION_HEADERS)

    ordered_urls: list[str] = []
    discovered_urls: set[str] = set(SEED_URLS)

    for seed_url in SEED_URLS:
        try:
            html = fetch(session, seed_url)
        except Exception as exc:
            print(f"failed to fetch seed {seed_url}: {exc}", file=sys.stderr)
            continue

        discovered_urls.add(seed_url)
        discovered_urls.update(extract_urls(html))

        for resource_id in resource_ids_from_html(html):
            try:
                resolved = resolve_resource_id(session, resource_id)
            except Exception as exc:
                print(f"failed to resolve resource id {resource_id}: {exc}", file=sys.stderr)
                continue
            if resolved:
                discovered_urls.add(resolved)
        time.sleep(0.1)

    ordered_urls = sorted(discovered_urls)

    records: list[DocRecord] = []
    for url in ordered_urls:
        try:
            html = fetch(session, url)
            record = parse_doc(url, html)
        except Exception as exc:
            print(f"failed to parse {url}: {exc}", file=sys.stderr)
            continue
        write_raw(url, html)
        write_doc(record)
        records.append(record)
        print(f"saved {record.section}: {record.title}", file=sys.stderr)
        time.sleep(0.1)

    summarize(records)
    print(json.dumps({"documents": len(records), "manifest": str(INDEX_DIR / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
