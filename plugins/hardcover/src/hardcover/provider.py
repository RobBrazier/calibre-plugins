import queue
import threading
from queue import Queue
from typing import Optional

try:
    from calibre.ebooks.metadata.book.base import Metadata  # noqa: F401
    from calibre.utils.logging import Log  # noqa: F401
except ImportError:
    pass
except AttributeError:
    pass

from graphql.client import GraphQLClient

from .identifier import HardcoverIdentifier
from .models import Book, Edition


class HardcoverProvider:
    ID_NAME = "hardcover"
    API_URL = "https://api.hardcover.app/v1/graphql"

    def __init__(self, source):
        self.source = source
        self.prefs = source.prefs
        self.client = GraphQLClient(self.API_URL)

    def get_book_url(self, identifiers):
        hardcover_id = identifiers.get(self.ID_NAME, None)
        if hardcover_id:
            return (
                self.ID_NAME,
                hardcover_id,
                f"https://hardcover.app/books/{hardcover_id}",
            )
        return None

    def identify(
        self,
        log,  # type: Log
        result_queue: queue.Queue,
        abort: threading.Event,
        title: Optional[str] = None,
        authors: Optional[list[str]] = None,
        identifiers={},
        timeout=30,
    ):
        identifier = HardcoverIdentifier(
            self.client, log, self.ID_NAME, self.prefs.get("api_key"), timeout
        )
        books = identifier.identify(title, authors, identifiers)

        for book in books:
            self.enqueue(log, result_queue, abort, book)
        return None

    def find_matching_edition(self, editions: list[Edition]):
        # TODO: do some actual matching here ...
        if len(editions) > 0:
            return editions[0]

    def init_metadata(self, title: str, authors: list[str]):
        from calibre.ebooks.metadata.book.base import Metadata

        return Metadata(title, authors)

    def build_metadata(self, log, book: Book):
        # type: (Log, Book) -> Optional[Metadata]
        editions = book.editions
        if len(editions) == 0:
            log.error("No matching edition")
            return None
        edition = editions[0]
        title = edition.title
        authors = edition.authors
        meta = self.init_metadata(title, authors)
        series = book.series
        if series:
            meta.series = series.name
            if series.position:
                meta.series_index = series.position  # pyright: ignore
        meta.set_identifier("hardcover", book.slug)
        meta.set_identifier("hardcover-edition", str(edition.id))
        if isbn := edition.isbn_13:
            meta.set_identifier("isbn", isbn)
            self.source.cache_isbn_to_identifier(isbn, book.slug)
        if book.description:
            meta.comments = book.description
        if edition.image:
            meta.has_cover = True
            self.source.cache_identifier_to_cover_url(book.slug, edition.image)
        else:
            meta.has_cover = False
        if edition.publisher:
            meta.publisher = edition.publisher
        if language := edition.language:
            meta.languages = [language]
        if book.rating:
            # hardcover rating is out of 5, calibre is out of 10
            meta.rating = book.rating * 2
        if edition.release_date:
            meta.pubdate = edition.release_date
        if book.tags:
            meta.tags = book.tags.tag
        return meta

    def enqueue(self, log, result_queue: Queue, shutdown: threading.Event, book: Book):
        # type: (Log, Queue, threading.Event, Book) -> None
        if shutdown.is_set():
            raise threading.ThreadError
        metadata = self.build_metadata(log, book)
        if metadata:
            result_queue.put(metadata)
            self.source.clean_downloaded_metadata(metadata)
        log.info(f"Adding book slug '{book.slug}' to queue")
