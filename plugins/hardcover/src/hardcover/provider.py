import queue
import threading
from datetime import datetime
from queue import Queue
from typing import Optional

try:
    from calibre.utils.logging import Log  # noqa: F401
    from calibre.ebooks.metadata.book.base import Metadata  # noqa: F401
except ImportError:
    pass
except AttributeError:
    pass

from .models import Book, Edition
from .identifier import HardcoverIdentifier


class HardcoverProvider:
    ID_NAME = "hardcover"

    identifier: Optional[HardcoverIdentifier]

    def __init__(self, source):
        self.source = source
        self.prefs = source.prefs

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
            log, self.ID_NAME, self.prefs.get("api_key"), timeout
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
        authors = [c.author.name for c in edition.contributions]
        meta = self.init_metadata(title, authors)
        book_series = book.book_series
        if len(book_series) > 0:
            series = book_series[0]
            meta.series = series.series.name
            meta.series_index = series.position  # pyright: ignore
        meta.set_identifier("hardcover", book.slug)
        meta.set_identifier("hardcover-edition", str(edition.id))
        if isbn := edition.isbn_13:
            meta.set_identifier("isbn", isbn)
            self.source.cache_isbn_to_identifier(isbn, book.slug)
        if book.description:
            meta.comments = book.description
        if edition.image.url:
            meta.has_cover = True
            self.source.cache_identifier_to_cover_url(book.slug, edition.image.url)
        else:
            meta.has_cover = False
        if edition.publisher:
            meta.publisher = edition.publisher.name
        if language := edition.language.code3:
            meta.languages = [language]
        if edition.release_date:
            try:
                meta.pubdate = datetime.strptime(edition.release_date, "%Y-%m-%d")
            except ValueError:
                log.warn("Unable to parse release date")
        if book.taggings:
            # you think this contains some tags?
            meta.tags = [tag.tag.tag for tag in book.taggings if tag.tag.tag]
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
