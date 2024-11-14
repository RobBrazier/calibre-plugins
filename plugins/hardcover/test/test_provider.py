from datetime import datetime
from queue import Queue
from threading import Event
import pytest
from unittest.mock import MagicMock, ANY

from hardcover.provider import HardcoverProvider
from .utils import create_book_response, create_edition, MockMetadata
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)


@pytest.fixture
def provider(mock_source, monkeypatch):
    provider_ = HardcoverProvider(mock_source)
    monkeypatch.setattr(
        provider_,
        "init_metadata",
        MagicMock(side_effect=lambda title, authors: MockMetadata(title, authors)),
    )
    return provider_


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
    provider: HardcoverProvider, mock_gql_client, monkeypatch
):
    result_queue = Queue()
    abort = Event()
    title = "The Hobbit"
    authors = ["J. R. R. Tolkien"]
    edition = "8548995"
    identifiers = {"hardcover-edition": edition}

    data = create_book_response(
        title=title,
        slug="the-hobbit",
        editions=[
            create_edition(
                title=title,
                id=int(edition),
                isbn="9780618968633",
                authors=authors,
                publisher="Houghton Mifflin Harcourt",
                release_date="1937-01-01",
            )
        ],
    )

    monkeypatch.setattr(provider, "client", mock_gql_client)

    mock_gql_client.execute.return_value = data

    provider.identify(logger, result_queue, abort, title, authors, identifiers)

    built_metadata = result_queue._get()
    assert built_metadata.title == title
    assert built_metadata.authors == authors
    assert built_metadata.identifiers == {
        "hardcover": "the-hobbit",
        "hardcover-edition": edition,
        "isbn": "9780618968633",
    }
    assert built_metadata.pubdate == datetime(1937, 1, 1)
    mock_gql_client.execute.assert_called_once_with(ANY, {"edition": edition}, 30)
