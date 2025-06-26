from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any


@dataclass
class Series:
    name: str
    position: Optional[float]


@dataclass
class Edition:
    id: int
    isbn_13: Optional[str]
    asin: Optional[str]
    title: str
    authors: List[str]
    image: Optional[str]
    language: str
    publisher: Optional[str]
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


def create_series(data: Optional[List[dict[str, Any]]]) -> Optional[Series]:
    if not data:
        return None
    series = data[0]
    return Series(name=series["series"]["name"], position=series["position"])


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
    return Edition(
        id=data["id"],
        isbn_13=data["isbn_13"],
        asin=data["asin"],
        title=data["title"],
        authors=[
            author["author"]["name"] for author in data.get("cached_contributors", [])
        ],
        image=data.get("cached_image", {}).get("url"),
        language=data.get("language", {}).get("code3", "eng")
        if data.get("language")
        else "eng",
        publisher=data.get("publisher", {}).get("name")
        if data.get("publisher")
        else None,
        release_date=datetime.strptime(data["release_date"], "%Y-%m-%d")
        if data["release_date"]
        else None,
    )


def map_from_edition_query(data: dict[str, Any]) -> Book:
    book = data["book"]
    return Book(
        id=book["id"],
        title=book["title"],
        slug=book["slug"],
        series=create_series(book["book_series"]),
        rating=book["rating"],
        tags=create_tags(book["cached_tags"]),
        description=book["description"],
        editions=[map_edition_data(data)],
    )


def map_from_book_query(data: dict[str, Any]) -> Book:
    return Book(
        id=data["id"],
        title=data["title"],
        slug=data["slug"],
        series=create_series(data["book_series"]),
        rating=data["rating"],
        tags=create_tags(data["cached_tags"]),
        description=data["description"],
        editions=[map_edition_data(edition) for edition in data.get("editions", [])],
    )
