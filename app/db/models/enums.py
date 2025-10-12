from enum import Enum


class PostStatus(str, Enum):
    draft = "draft"
    published = "published"


class PostCategory(str, Enum):
    free = "free"
    dev = "dev"
    celeb = "celeb"
    love = "love"
    work = "work"
    book = "book"
    health = "health"