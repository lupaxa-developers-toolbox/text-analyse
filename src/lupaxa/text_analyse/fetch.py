"""Fetch a URL and return the text worth analysing."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

from lupaxa.text_analyse.constants import DEFAULT_TIMEOUT, MAX_BODY_BYTES
from lupaxa.text_analyse.exceptions import FetchError
from lupaxa.text_analyse.version import __version__


@dataclass(frozen=True)
class Fetched:
    """Text downloaded from a URL."""

    text: str
    is_html: bool


def user_agent() -> str:
    """User-Agent sent when fetching a URL."""
    return (
        f"text-analyse/{__version__} (+https://github.com/lupaxa-developers-toolbox/text-analyse)"
    )


def fetch(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_BODY_BYTES,
) -> Fetched:
    """Download ``url``.

    HTML responses drop navigation, headers, footers, and sidebars, then
    keep headings, paragraphs, and list items from the article.
    Anything else is decoded as-is. Bodies larger than ``max_bytes`` raise
    :class:`FetchError`.
    """
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    try:
        with (
            httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": user_agent()},
            ) as client,
            client.stream("GET", url) as response,
        ):
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise FetchError(f"Error fetching URL: HTTP {exc.response.status_code}") from exc
            raw = _read_limited(response, max_bytes)
            encoding = response.charset_encoding or "utf-8"
            content_type = response.headers.get("Content-Type", "")
    except FetchError:
        raise
    except httpx.HTTPError as exc:
        raise FetchError(f"Error fetching URL: {exc}") from exc

    decoded = raw.decode(encoding, errors="replace")
    is_html = _is_html(content_type, decoded)
    if is_html:
        return Fetched(text=_html_to_text(decoded), is_html=True)
    return Fetched(text=decoded, is_html=False)


def fetch_text(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_BODY_BYTES,
) -> str:
    """Download ``url`` and return the extracted text."""
    return fetch(url, timeout=timeout, max_bytes=max_bytes).text


def _is_html(content_type: str, raw_text: str) -> bool:
    if "html" in content_type.lower():
        return True
    sample = raw_text.lstrip()[:256].lower()
    return sample.startswith("<!doctype html") or sample.startswith("<html")


def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise FetchError(f"Error fetching URL: response exceeds {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


_BLOCK_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li")
_CHROME_ROLES = {"navigation", "banner", "contentinfo"}
_CHROME_HINTS = (
    "toc",
    "sidebar",
    "table-of-contents",
    "md-sidebar",
    "md-nav",
    "breadcrumb",
)


def _html_to_text(html: str) -> str:
    """Return the article text, with one blank line between blocks.

    Drops scripts, styles, navigation, headers, footers, and sidebars.
    Headings, paragraphs, and list items each become a paragraph.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in list(soup.find_all(True)):
        if tag.parent is not None and _is_chrome(tag):
            tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[str] = []
    for element in root.find_all(_BLOCK_TAGS):
        if element.find_parent(_BLOCK_TAGS) is not None:
            continue
        text = " ".join(element.get_text(" ", strip=True).split())
        if text:
            blocks.append(text)
    if blocks:
        return "\n\n".join(blocks)
    return " ".join(root.get_text(" ", strip=True).split())


def _is_chrome(tag: Tag) -> bool:
    if tag.name in {"script", "style", "noscript", "svg", "header", "footer", "nav", "aside"}:
        return True
    role = str(tag.get("role") or "").lower()
    if role in _CHROME_ROLES:
        return True
    class_value = tag.get("class")
    if isinstance(class_value, str):
        class_text = class_value
    elif isinstance(class_value, list):
        class_text = " ".join(str(item) for item in class_value)
    else:
        class_text = ""
    blob = f"{class_text} {tag.get('id') or ''}".lower()
    return any(hint in blob for hint in _CHROME_HINTS)
