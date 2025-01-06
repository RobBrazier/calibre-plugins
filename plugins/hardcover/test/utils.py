from typing import Any
from types import SimpleNamespace


class MockMetadata(SimpleNamespace):
    def __init__(self, title: str, authors: list[str]) -> None:
        super().__init__()
        self.__dict__.update({"title": title, "authors": authors})

    def set_identifier(self, key, value):
        identifiers = self.__dict__.get("identifiers", {})
        identifiers.update({key: value})
        self.__dict__.update({"identifiers": identifiers})


def create_edition(
    title: str,
    id: int,
    isbn: str = "",
    authors: list[str] = [],
    image_url: str = "",
    language: str = "eng",
    publisher: str = "",
    release_date: str = "",
):
    edition: dict[str, Any] = {
        "id": id,
        "title": title,
        "isbn_13": isbn,
        "asin": None,
        "cached_contibutors": [{"author": {"name": name}} for name in authors],
        "language": {"code3": language},
        "release_date": release_date,
        "description": None,
    }

    if image_url:
        edition.update({"cached_image": {"url": image_url}})
    if publisher:
        edition.update({"publisher": {"name": publisher}})
    return edition


def create_book_response(
    title: str,
    slug: str,
    series_name: str = "",
    series_position: int = 0,
    tags: list[str] = [],
    editions: list[dict] = [],
    description: str = "",
    unwrapped=False,
):
    book: dict[str, Any] = {
        "id": 0,
        "title": title,
        "slug": slug,
        "description": description,
        "editions": editions,
        "rating": 5.0,
        "book_series": {},
        "cached_tags": {"Tags": [{"tag": {"tag": tag}} for tag in tags]},
    }
    if series_name or series_position:
        book.update(
            {
                "book_series": {
                    "series": {"name": series_name},
                    "position": series_position,
                }
            }
        )
    if unwrapped:
        return book
    return {"books": [book]}
