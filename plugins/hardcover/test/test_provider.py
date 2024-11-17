import pytest
from unittest.mock import MagicMock

from hardcover.provider import HardcoverProvider
from .utils import MockMetadata
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
