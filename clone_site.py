#!/usr/bin/env python3
"""Simple website cloner for a single domain.

Usage:
  python clone_site.py https://example.com --output cloned_site --max-pages 200
"""

from __future__ import annotations

import argparse
import pathlib
import re
from collections import deque
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ASSET_ATTRS = {
    "img": ["src", "srcset"],
    "script": ["src"],
    "link": ["href"],
    "source": ["src", "srcset"],
    "video": ["src", "poster"],
    "audio": ["src"],
}


def sanitize_path(url: str) -> pathlib.Path:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path.endswith("/"):
        path += "index.html"
    if not pathlib.Path(path).suffix:
        path += ".html"
    safe = re.sub(r"[^a-zA-Z0-9._/\\-]", "_", path.lstrip("/"))
    return pathlib.Path(safe)


def is_same_domain(base_netloc: str, candidate: str) -> bool:
    c = urlparse(candidate)
    return c.netloc == "" or c.netloc == base_netloc


def normalize_url(base: str, link: str) -> str:
    joined = urljoin(base, link)
    cleaned, _frag = urldefrag(joined)
    return cleaned


def iter_links(soup: BeautifulSoup, page_url: str) -> Iterable[str]:
    for tag, attrs in ASSET_ATTRS.items():
        for node in soup.find_all(tag):
            for attr in attrs:
                value = node.get(attr)
                if not value:
                    continue
                if attr == "srcset":
                    for part in value.split(","):
                        src = part.strip().split(" ")[0]
                        if src:
                            yield normalize_url(page_url, src)
                else:
                    yield normalize_url(page_url, value)

    for node in soup.find_all("a"):
        href = node.get("href")
        if href:
            yield normalize_url(page_url, href)


def save_binary(content: bytes, out_file: pathlib.Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(content)


def rewrite_links(soup: BeautifulSoup, current_url: str, domain: str) -> str:
    def relink(val: str) -> str:
        target = normalize_url(current_url, val)
        if not is_same_domain(domain, target):
            return val
        target_path = sanitize_path(target)
        return str(target_path).replace("\\", "/")

    for tag, attrs in ASSET_ATTRS.items():
        for node in soup.find_all(tag):
            for attr in attrs:
                value = node.get(attr)
                if not value:
                    continue
                if attr == "srcset":
                    rewritten = []
                    for part in value.split(","):
                        pieces = part.strip().split(" ")
                        if not pieces:
                            continue
                        pieces[0] = relink(pieces[0])
                        rewritten.append(" ".join(pieces))
                    node[attr] = ", ".join(rewritten)
                else:
                    node[attr] = relink(value)

    for node in soup.find_all("a"):
        href = node.get("href")
        if href:
            node["href"] = relink(href)

    return str(soup)


def clone_site(start_url: str, output: pathlib.Path, max_pages: int, timeout: float) -> None:
    parsed = urlparse(start_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("start_url must be an absolute URL (e.g. https://example.com)")

    domain = parsed.netloc
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; SiteCloner/1.0)"})

    q = deque([start_url])
    seen: set[str] = set()
    page_count = 0

    while q and page_count < max_pages:
        url = q.popleft()
        if url in seen or not is_same_domain(domain, url):
            continue
        seen.add(url)

        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[warn] failed: {url} ({exc})")
            continue

        content_type = resp.headers.get("content-type", "")
        out_file = output / sanitize_path(url)

        if "text/html" in content_type or out_file.suffix in {".html", ".htm"}:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in iter_links(soup, url):
                if is_same_domain(domain, link) and link not in seen:
                    q.append(link)
            html = rewrite_links(soup, url, domain)
            save_binary(html.encode("utf-8"), out_file)
            page_count += 1
            print(f"[page] {url} -> {out_file}")
        else:
            save_binary(resp.content, out_file)
            print(f"[asset] {url} -> {out_file}")

    print(f"Done. Saved into: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clone a website into static local files.")
    parser.add_argument("url", help="Start URL, e.g. https://imageconverttools.site")
    parser.add_argument("--output", default="cloned_site", help="Output folder")
    parser.add_argument("--max-pages", type=int, default=200, help="Maximum HTML pages to crawl")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")

    args = parser.parse_args()
    clone_site(args.url, pathlib.Path(args.output), args.max_pages, args.timeout)


if __name__ == "__main__":
    main()
