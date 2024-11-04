from dataclasses import dataclass
from typing import List, Dict, Any, cast, TypeVar

T = TypeVar("T")


def safe_default(input: dict, key: str, defaultValue: T) -> T:
    if input.get(key):
        return cast(T, input.get(key))
    return defaultValue


@dataclass
class Author:
    name: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(name=safe_default(data, "name", ""))


@dataclass
class Contribution:
    author: Author

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(author=Author.from_dict(safe_default(data, "author", {})))


@dataclass
class Tag:
    tag: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(tag=safe_default(data, "tag", ""))


@dataclass
class Tagging:
    tag: Tag

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(tag=Tag.from_dict(safe_default(data, "tag", {})))


@dataclass
class Image:
    url: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(url=safe_default(data, "url", ""))


@dataclass
class Edition:
    asin: str
    isbn_13: str
    isbn_10: str
    title: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            asin=safe_default(data, "asin", ""),
            isbn_13=safe_default(data, "isbn_13", ""),
            isbn_10=safe_default(data, "isbn_10", ""),
            title=safe_default(data, "title", ""),
        )


@dataclass
class Series:
    name: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=safe_default(data, "name", ""),
        )


@dataclass
class BookSeries:
    series: Series
    position: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            series=Series.from_dict(safe_default(data, "series", {})),
            position=safe_default(data, "position", 0),
        )


@dataclass
class Book:
    title: str
    slug: str
    users_read_count: int
    contributions: List[Contribution]
    release_date: str
    book_series: List[BookSeries]
    taggings: List[Tagging]
    image: Image
    editions: List[Edition]
    description: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            title=safe_default(data, "title", ""),
            slug=safe_default(data, "slug", ""),
            users_read_count=safe_default(data, "users_read_count", 0),
            contributions=[
                Contribution.from_dict(c)
                for c in safe_default(data, "contributions", [])
            ],
            release_date=safe_default(data, "release_date", ""),
            book_series=[
                BookSeries.from_dict(t) for t in safe_default(data, "book_series", [])
            ],
            taggings=[Tagging.from_dict(t) for t in safe_default(data, "taggings", [])],
            image=Image.from_dict(safe_default(data, "image", {})),
            editions=[Edition.from_dict(e) for e in safe_default(data, "editions", [])],
            description=safe_default(data, "description", ""),
        )
