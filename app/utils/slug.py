from __future__ import annotations

import re
from typing import Iterable

RESERVED_SLUGS = {"admin", "api", "auth", "login", "signup", "root", "posts", "me"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9\-\s]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


def is_valid_slug(value: str, *, min_length: int = 3, max_length: int = 30) -> bool:
    if not (min_length <= len(value) <= max_length):
        return False
    if value in RESERVED_SLUGS:
        return False
    return bool(SLUG_PATTERN.fullmatch(value))


def ensure_unique_slug(base: str, existing: Iterable[str]) -> str:
    slug = normalize_slug(base)
    if slug not in existing:
        return slug
    counter = 2
    while True:
        candidate = f"{slug}-{counter}"
        if candidate not in existing:
            return candidate
        counter += 1
