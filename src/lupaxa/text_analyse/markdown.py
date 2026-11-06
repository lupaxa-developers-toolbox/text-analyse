"""Drop Markdown markup that would distort a readability score."""

from __future__ import annotations

import re

_CLOSED_FENCE_RE = re.compile(
    r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})[^\n]*\n(?:.*\n)*?[ ]{0,3}(?P=fence)[ \t]*\n?",
    re.MULTILINE,
)
_OPEN_FENCE_RE = re.compile(
    r"^[ ]{0,3}(`{3,}|~{3,})[^\n]*(?:\n.*)?\Z",
    re.MULTILINE | re.DOTALL,
)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_REF_DEF_RE = re.compile(r"^[ ]{0,3}\[[^\]]+\]:[ \t]+\S+[^\n]*$", re.MULTILINE)
_HTML_TAG_RE = re.compile(r"</?[A-Za-z!][^>\n]*>")
_URL_RE = re.compile(r"https?://\S+")


def strip_markdown(text: str) -> str:
    """Remove fenced code, HTML tags, and link URLs. Leave the prose."""
    stripped = _CLOSED_FENCE_RE.sub("\n", text)
    stripped = _OPEN_FENCE_RE.sub("\n", stripped)
    stripped = _HTML_COMMENT_RE.sub("", stripped)
    stripped = _IMAGE_RE.sub(r"\1", stripped)
    stripped = _LINK_RE.sub(r"\1", stripped)
    stripped = _REF_DEF_RE.sub("", stripped)
    stripped = _HTML_TAG_RE.sub("", stripped)
    return _URL_RE.sub("", stripped)
