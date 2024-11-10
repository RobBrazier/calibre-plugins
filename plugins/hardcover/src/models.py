from dataclasses import dataclass
from typing import List, Dict, Any
from common.utils import safe_default


@dataclass
class Author:
    name: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(name=safe_default(data, "name", ""))


@dataclass
class Publisher:
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
class Language:
    code3: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            code3=safe_default(data, "code3", ""),
        )


@dataclass
class Edition:
    id: int
    isbn_13: str
    title: str
    contributions: List[Contribution]
    image: Image
    language: Language
    publisher: Publisher
    release_date: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            id=safe_default(data, "id", 0),
            isbn_13=safe_default(data, "isbn_13", ""),
            title=safe_default(data, "title", ""),
            contributions=[
                Contribution.from_dict(c)
                for c in safe_default(data, "contributions", [])
            ],
            image=Image.from_dict(safe_default(data, "image", {})),
            language=Language.from_dict(safe_default(data, "language", {})),
            publisher=Publisher.from_dict(safe_default(data, "publisher", {})),
            release_date=safe_default(data, "release_date", ""),
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
    book_series: List[BookSeries]
    taggings: List[Tagging]
    editions: List[Edition]
    description: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            title=safe_default(data, "title", ""),
            slug=safe_default(data, "slug", ""),
            users_read_count=safe_default(data, "users_read_count", 0),
            book_series=[
                BookSeries.from_dict(t) for t in safe_default(data, "book_series", [])
            ],
            taggings=[Tagging.from_dict(t) for t in safe_default(data, "taggings", [])],
            editions=[Edition.from_dict(e) for e in safe_default(data, "editions", [])],
            description=safe_default(data, "description", ""),
        )
