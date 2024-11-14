from datetime import datetime
from queue import Queue
from threading import Event
from types import SimpleNamespace
from typing import Any
from common.graphql import GraphQLClient
import pytest
from unittest.mock import MagicMock

from hardcover.provider import HardcoverProvider
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_source():
    return MagicMock()


class MockMetadata(SimpleNamespace):
    def __init__(self, title: str, authors: list[str]) -> None:
        super().__init__()
        self.__dict__.update({"title": title, "authors": authors})

    def set_identifier(self, key, value):
        identifiers = self.__dict__.get("identifiers", {})
        identifiers.update({key: value})
        self.__dict__.update({"identifiers": identifiers})


@pytest.fixture
def provider(mock_source, monkeypatch):
    provider_ = HardcoverProvider(mock_source)
    monkeypatch.setattr(
        provider_,
        "init_metadata",
        MagicMock(side_effect=lambda title, authors: MockMetadata(title, authors)),
    )
    return provider_


@pytest.fixture
def mock_client():
    return MagicMock(spec=GraphQLClient)()


def test_get_book_url_no_identifier(provider: HardcoverProvider):
    identifiers = {}
    assert provider.get_book_url(identifiers) is None


def test_get_book_url_with_identifier(provider: HardcoverProvider):
    identifiers = {"hardcover": "the-hobbit"}
    expected = (
        HardcoverProvider.ID_NAME,
        "the-hobbit",
        "https://hardcover.app/books/the-hobbit",
    )
    result = provider.get_book_url(identifiers)
    assert result == expected


def test_identify_hardcover_edition(
    provider: HardcoverProvider, mock_client, monkeypatch
):
    result_queue = Queue()
    abort = Event()
    title = "The Hobbit"
    authors = ["J. R. R. Tolkien"]
    identifiers = {"hardcover-edition": "8548995"}

    data = create_book_response(
        title=title,
        slug="the-hobbit",
        editions=[
            create_edition(
                title=title,
                id=8548995,
                isbn="9780618968633",
                authors=authors,
                publisher="Houghton Mifflin Harcourt",
                release_date="1937-01-01",
            )
        ],
    )

    monkeypatch.setattr(provider, "client", mock_client)

    mock_client.execute.return_value = data

    provider.identify(logger, result_queue, abort, title, authors, identifiers)

    built_metadata = result_queue._get()
    assert built_metadata.title == title
    assert built_metadata.authors == authors
    assert built_metadata.identifiers == {
        "hardcover": "the-hobbit",
        "hardcover-edition": "8548995",
        "isbn": "9780618968633",
    }
    assert built_metadata.pubdate == datetime.fromisoformat("1937-01-01")


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
        "contributions": [{"author": {"name": name}} for name in authors],
        "language": {"code3": language},
        "release_date": release_date,
    }

    if image_url:
        edition.update({"image": {"url": image_url}})
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
        "title": title,
        "slug": slug,
        "description": description,
        "editions": editions,
        "book_series": {},
        "taggings": [{"tag": {"tag": tag}} for tag in tags],
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
