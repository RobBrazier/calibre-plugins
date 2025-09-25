from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any


@dataclass
class Series:
    name: str
    position: Optional[float]


@dataclass
class Author:
    name: str
    contribution: str


@dataclass
class Edition:
    id: int
    isbn_13: Optional[str]
    asin: Optional[str]
    title: str
    authors: List[Author]
    image: Optional[str]
    language: Optional[str]
    publisher: Optional[str]
    users_count: int
    release_date: Optional[datetime]


@dataclass
class Tags:
    genre: List[str]
    mood: List[str]
    content_warning: List[str]
    tag: List[str]


@dataclass
class Book:
    id: int
    title: str
    slug: str
    series: Optional[Series]
    rating: Optional[float]
    tags: Optional[Tags]
    description: Optional[str]
    editions: List[Edition]
    canonical_id: Optional[int]


def create_authors(data: Optional[list[dict[str, Any]]]) -> list[Author]:
    if not data:
        return []
    authors = []
    for entry in data:
        author = entry.get("author", {})
        name = author.get("name")
        contribution = entry.get("contribution") or "Author"
        authors.append(Author(name, contribution))
    return authors


def create_series(data: Optional[dict[str, Any]]) -> Optional[Series]:
    if not data:
        return None
    return Series(name=data["series"]["name"], position=data["position"])


def create_tags(data: Optional[dict[str, Any]]) -> Optional[Tags]:
    if not data:
        return None
    return Tags(
        genre=[tag["tag"] for tag in data.get("Genre", [])],
        mood=[tag["tag"] for tag in data.get("Mood", [])],
        content_warning=[tag["tag"] for tag in data.get("Content Warning", [])],
        tag=[tag["tag"] for tag in data.get("Tag", [])],
    )


def map_edition_data(data: dict[str, Any]) -> Edition:
    release_date = (
        datetime.strptime(data["release_date"], "%Y-%m-%d")
        if data["release_date"]
        else None
    )
    return Edition(
        id=data["id"],
        isbn_13=data["isbn_13"],
        asin=data["asin"],
        title=data["title"],
        authors=create_authors(data.get("contributors", [])),
        image=(data.get("image") or {}).get("url"),
        language=(data.get("language") or {}).get("code3"),
        publisher=(data.get("publisher") or {}).get("name"),
        users_count=data.get("users_count", 0),
        release_date=release_date,
    )


def map_from_edition_query(data: dict[str, Any]) -> Book:
    book = data["book"]
    return Book(
        id=book["id"],
        title=book["title"],
        slug=book["slug"],
        series=create_series(book["series"]),
        rating=book["rating"],
        tags=create_tags(book["tags"]),
        description=book["description"],
        editions=[map_edition_data(data)],
        canonical_id=book["canonical_id"],
    )


def map_from_book_query(data: dict[str, Any]) -> Book:
    return Book(
        id=data["id"],
        title=data["title"],
        slug=data["slug"],
        series=create_series(data["series"]),
        rating=data["rating"],
        tags=create_tags(data["tags"]),
        description=data["description"],
        editions=[map_edition_data(edition) for edition in data.get("editions", [])],
        canonical_id=data["canonical_id"],
    )
