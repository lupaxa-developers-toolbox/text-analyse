"""Tests for URL fetching."""

from __future__ import annotations

import httpx
import pytest

from lupaxa.text_analyse.exceptions import FetchError
from lupaxa.text_analyse.fetch import fetch, fetch_text, user_agent
from lupaxa.text_analyse.text import analyse_text

_RealClient = httpx.Client


def _patch_client(monkeypatch: pytest.MonkeyPatch, handler: object) -> None:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]

    def factory(*_args: object, **kwargs: object) -> httpx.Client:
        headers = kwargs.get("headers")
        return _RealClient(transport=transport, headers=headers)  # type: ignore[arg-type]

    monkeypatch.setattr("lupaxa.text_analyse.fetch.httpx.Client", factory)


def test_html_body_drops_script_and_style(monkeypatch: pytest.MonkeyPatch) -> None:
    html = (
        "<html><body><script>secret</script><style>.x{}</style>"
        "<noscript>hidden</noscript><p>Hello there.</p></body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["user-agent"] == user_agent()
        return httpx.Response(200, headers={"Content-Type": "text/html; charset=utf-8"}, text=html)

    _patch_client(monkeypatch, handler)
    assert fetch_text("https://example.test/article") == "Hello there."
    assert fetch("https://example.test/article").is_html is True


def test_html_keeps_the_article_and_drops_chrome(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html><body>
      <header>Skip to content</header>
      <nav>Home</nav>
      <aside class="md-sidebar">Table of contents</aside>
      <article>
        <h2>Who We Are</h2>
        <p>The project builds tools.</p>
        <p>It is open.</p>
        <ul><li>One</li><li>Two</li></ul>
      </article>
      <footer>Copyright</footer>
    </body></html>
    """

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/html"}, text=html)

    _patch_client(monkeypatch, handler)
    text = fetch_text("https://example.test/page")
    assert "Who We Are" in text
    assert "The project builds tools." in text
    assert "One" in text
    assert "Skip to content" not in text
    assert "Table of contents" not in text
    assert "Copyright" not in text
    assert analyse_text(text)["paragraphs"] == 5


def test_plain_text_is_returned_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/plain"}, text="alpha beta")

    _patch_client(monkeypatch, handler)
    assert fetch_text("https://example.test/notes.txt") == "alpha beta"


def test_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing")

    _patch_client(monkeypatch, handler)
    with pytest.raises(FetchError, match="HTTP 404"):
        fetch_text("https://example.test/missing")


def test_body_over_the_size_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/plain"}, text="hello world")

    _patch_client(monkeypatch, handler)
    with pytest.raises(FetchError, match="exceeds 4 bytes"):
        fetch_text("https://example.test/big", max_bytes=4)


def test_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("nope")

    _patch_client(monkeypatch, handler)
    with pytest.raises(FetchError, match="Error fetching URL"):
        fetch_text("https://example.test/down")
