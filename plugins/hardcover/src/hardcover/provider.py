import queue
import threading
from queue import Queue
from typing import Optional

from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.logging import Log

from graphql.client import GraphQLClient

from .identifier import HardcoverIdentifier
from .models import Book
from ._version import __version__


class HardcoverProvider:
    ID_NAME = "hardcover"
    API_URL = "https://api.hardcover.app/v1/graphql"

    def __init__(self, source):
        self.source = source
        self.prefs = source.prefs
        useragent = f"hardcover-calibre-plugin/{__version__} (https://github.com/RobBrazier/calibre-plugins)"
        self.client = GraphQLClient(self.API_URL, useragent)

    def get_book_url(self, identifiers) -> tuple[str, str, str] | None:
        hardcover_id: str | None = identifiers.get(self.ID_NAME, None)
        if hardcover_id:
            return (
                self.ID_NAME,
                hardcover_id,
                f"https://hardcover.app/books/{hardcover_id}",
            )
        return None

    def identify(
        self,
        log: Log,
        result_queue: queue.Queue,
        abort: threading.Event,
        title: Optional[str] = None,
        authors: Optional[list[str]] = None,
        identifiers={},
        timeout=30,
    ):
        identifier = HardcoverIdentifier(
            self.client,
            log,
            self.ID_NAME,
            self.prefs.get("api_key"),
            self.prefs.get("match_sensitivity"),
            self.prefs.get("languages").split(","),
            timeout,
        )
        books = identifier.identify(title, authors, identifiers)

        for book in books:
            self.enqueue(log, result_queue, abort, book)
        return None

    def init_metadata(self, title: str, authors: list[str]):
        return Metadata(title, authors)

    def build_metadata(self, log: Log, book: Book):
        edition = next(iter(book.editions), None)
        if not edition:
            log.error("No matching edition")
            return None
        title = edition.title
        authors = [author.name for author in edition.authors]
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
            # Combine Tags and Genre
            meta.tags = book.tags.tag + book.tags.genre
        return meta

    def enqueue(
        self, log: Log, result_queue: Queue, shutdown: threading.Event, book: Book
    ):
        if shutdown.is_set():
            raise threading.ThreadError
        metadata = self.build_metadata(log, book)
        if metadata:
            result_queue.put(metadata)
            self.source.clean_downloaded_metadata(metadata)
        log.info(f"Adding book slug '{book.slug}' to queue")
