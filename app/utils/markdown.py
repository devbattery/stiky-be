from __future__ import annotations

import bleach
from markdown_it import MarkdownIt

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union(
    {
        "p",
        "pre",
        "code",
        "img",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "blockquote",
    }
)
ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "img": {"src", "alt", "title"},
    "a": {"href", "title", "rel"},
}

md = MarkdownIt("commonmark", {
    "typographer": True,
})


def markdown_to_html(markdown_text: str) -> str:
    rendered = md.render(markdown_text)
    sanitized = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    return sanitized
