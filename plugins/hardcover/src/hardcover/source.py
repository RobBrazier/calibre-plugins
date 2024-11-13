# pyright: reportIncompatibleMethodOverride=false
import threading
from datetime import datetime
from queue import Empty, Queue
from typing import List, Tuple

from calibre.ebooks.metadata.book.base import Metadata
from calibre.ebooks.metadata.sources.base import Option, Source
from calibre.utils.logging import Log

from . import queries
from .__version__ import __version_tuple__
from .models import Book, Edition


class Hardcover(Source):
    name = "Hardcover"
    description = "Downloads metadata and covers from Hardcover.app"
    author = "Rob Brazier"
    version = __version_tuple__
    minimum_calibre_version = (7, 7, 0)

    ID_NAME = "hardcover"
    API_URL = "https://api.hardcover.app/v1/graphql"

    capabilities = frozenset(["identify", "cover"])
    touched_fields = frozenset(
        [
            "title",
            "authors",
            f"identifier:{ID_NAME}",
            f"identifier:{ID_NAME}-edition",
            "pubdate",
            "series",
            "tags",
        ]
    )
    options = (
        Option(
            name="api_key",
            type_="string",
            default="",
            label=_("API Key"),  # noqa: F821
            desc=_("Hardcover API Key"),  # noqa: F821
        ),
    )

    def __init__(self, *args, **kwargs):
        Source.__init__(self, *args, **kwargs)
        with self:
            from common.graphql import GraphQLClient

            self.client = GraphQLClient(self.API_URL)

    def is_configured(self):
        return bool(self.prefs["api_key"])

    def _execute(self, query, variables=None, timeout=30):
        if not self.client.token:
            self.client.set_token(self.prefs["api_key"])

        books = self.client.execute(query, variables, timeout)
        result: List[Book] = []
        if "books" not in books:
            return result
        for entry in books.get("books", []):
            result.append(Book.from_dict(entry))
        return result

    def get_book_url(self, identifiers):
        hardcover_id = identifiers.get(self.ID_NAME, None)
        if hardcover_id:
            return (
                self.ID_NAME,
                hardcover_id,
                f"https://hardcover.app/books/{hardcover_id}",
            )
        return None

    def cli_main(self, args):
        from common.cli import MetadataCliHelper

        MetadataCliHelper(self, self.name, self.ID_NAME).run(args)

    def identify(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
    ):
        hardcover_id = identifiers.get(self.ID_NAME, None)
        hardcover_edition = identifiers.get(f"{self.ID_NAME}-edition", None)
        isbn = identifiers.get("isbn", "")
        asin = identifiers.get("mobi-asin", "")

        found_exact = False
        candidate_books = []

        # Exact match with a Hardcover Edition ID
        if hardcover_edition:
            books = self.get_book_by_edition(log, hardcover_edition, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Exact match with a Hardcover ID
        if hardcover_id and not found_exact:
            books = self.get_book_by_slug(log, hardcover_id, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Exact match with an ISBN or ASIN
        if (isbn or asin) and not found_exact:
            books = self.get_book_by_isbn_asin(log, isbn, asin, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Search for an Exact match by Fuzzy Title and Authors
        if title and authors and not found_exact:
            books = self.get_book_by_name_authors(log, title, authors, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Fuzzy Search by Title
        if title and not found_exact:
            books = self.get_book_by_name(log, title, timeout)

            candidate_books = books

            # Get closest books by Title
            candidate_titles: List[Tuple[int, Book]] = []
            for book in candidate_books:
                similarity = self.levenshtein_distance(title, book.title)
                candidate_titles.append((similarity, book))
            candidate_titles = sorted(candidate_titles, key=lambda x: x[0])
            if len(candidate_titles) > 20:
                candidate_titles = candidate_titles[:20]
            candidate_books = [book[1] for book in candidate_titles]

            # Get closest books by Author
            # candidate_authors: List[Tuple[int, Book]] = []
            # if authors:
            #     for book in candidate_books:
            #         book_authors = [c.author.name for c in book.contributions]
            #         similarity = self.similar_authors(authors, book_authors)
            #         candidate_authors.append((similarity, book))
            #     candidate_authors = sorted(candidate_authors, key=lambda x: x[0])
            #     if len(candidate_authors) > 10:
            #         candidate_authors = candidate_authors[:10]
            #
            #     candidate_books = [book[1] for book in candidate_authors]

        for book in candidate_books:
            self.enqueue(log, result_queue, abort, book)
        return None

    def get_cached_cover_url(self, identifiers):
        url = None
        hardcover_id = identifiers.get(self.ID_NAME, None)
        if hardcover_id is None:
            isbn = identifiers.get("isbn", None)
            if isbn is not None:
                hardcover_id = self.cached_isbn_to_identifier(isbn)
        if hardcover_id is not None:
            url = self.cached_identifier_to_cover_url(hardcover_id)
        return url

    def download_cover(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
        get_best_cover=False,
    ):
        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url is None:
            log.info("No cached cover found, running identify")
            rq = Queue()
            self.identify(
                log, rq, abort, title=title, authors=authors, identifiers=identifiers
            )
            if abort.is_set():
                return
            results = []
            while True:
                try:
                    results.append(rq.get_nowait())
                except Empty:
                    break
            results.sort(
                key=self.identify_results_keygen(
                    title=title, authors=authors, identifiers=identifiers
                )
            )
            for mi in results:
                cached_url = self.get_cached_cover_url(mi.identifiers)
                if cached_url is not None:
                    break
        if cached_url is None:
            log.info("No cover found")
            return

        if abort.is_set():
            return

        log("Downloading cover from: ", cached_url)
        try:
            cdata = self.browser.open_novisit(cached_url, timeout=timeout).read()
            result_queue.put((self, cdata))
        except Exception:
            log.exception("Failed to download cover from: ", cached_url)

    @staticmethod
    def levenshtein_distance(s1, s2):
        if len(s1) > len(s2):
            s1, s2 = s2, s1

        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2 + 1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(
                        1 + min((distances[i1], distances[i1 + 1], distances_[-1]))
                    )
            distances = distances_
        return distances[-1]

    def similar_authors(self, metadata_author, book_author):
        source = ",".join(sorted(metadata_author))
        target = ",".join(sorted(book_author))
        return self.levenshtein_distance(source, target)

    def find_matching_edition(self, editions: List[Edition]):
        if len(editions) > 0:
            return editions[0]

    def build_metadata(self, log, book: Book):
        editions = book.editions
        matching_edition = self.find_matching_edition(editions)
        if not matching_edition:
            log.error("No matching edition")
            return None
        title = matching_edition.title
        authors = [c.author.name for c in matching_edition.contributions]
        meta = Metadata(title, authors)
        book_series = book.book_series
        if len(book_series) > 0:
            series = book_series[0]
            meta.series = series.series.name
            meta.series_index = series.position  # pyright: ignore
        meta.set_identifier("hardcover", book.slug)
        meta.set_identifier("hardcover-edition", str(matching_edition.id))
        if isbn := matching_edition.isbn_13:
            meta.set_identifier("isbn", isbn)
            self.cache_isbn_to_identifier(isbn, book.slug)
        if book.description:
            meta.comments = book.description
        if matching_edition.image.url:
            meta.has_cover = True
            self.cache_identifier_to_cover_url(book.slug, matching_edition.image.url)
        else:
            meta.has_cover = False
        if matching_edition.publisher:
            meta.publisher = matching_edition.publisher.name
        if language := matching_edition.language.code3:
            meta.languages = [language]
        if matching_edition.release_date:
            try:
                meta.pubdate = datetime.strptime(
                    matching_edition.release_date, "%Y-%m-%d"
                )
            except ValueError:
                log.warn("Unable to parse release date")
        if book.taggings:
            meta.tags = [tag.tag.tag for tag in book.taggings if tag.tag.tag]
        return meta

    def enqueue(
        self, log: Log, result_queue: Queue, shutdown: threading.Event, book: Book
    ):
        if shutdown.is_set():
            raise threading.ThreadError
        metadata = self.build_metadata(log, book)
        if metadata:
            result_queue.put(metadata)
            self.clean_downloaded_metadata(metadata)
        log.info(f"Adding book slug '{book.slug}' to queue")

    def get_book_by_isbn_asin(
        self, log: Log, isbn: str, asin: str, timeout=30
    ) -> list[Book]:
        log.info("Finding by ISBN / ASIN")
        query = queries.FIND_BOOK_BY_ISBN_OR_ASIN
        vars = {"isbn": isbn, "asin": asin}
        return self._execute(query, vars, timeout)

    def get_book_by_slug(self, log: Log, slug: str, timeout=30) -> list[Book]:
        log.info("Finding by Slug")
        query = queries.FIND_BOOK_BY_SLUG
        vars = {"slug": slug}
        return self._execute(query, vars, timeout)

    def get_book_by_edition(self, log: Log, edition: str, timeout=30) -> list[Book]:
        log.info("Finding by Edition ID")
        query = queries.FIND_BOOK_BY_EDITION
        vars = {"edition": edition}
        return self._execute(query, vars, timeout)

    def get_book_by_name(self, log: Log, name: str, timeout=30) -> list[Book]:
        log.info("Finding by Name")
        query = queries.FIND_BOOK_BY_NAME
        vars = {"title": name}
        return self._execute(query, vars, timeout)

    def get_book_by_name_authors(
        self, log: Log, name: str, authors: List[str], timeout=30
    ) -> list[Book]:
        log.info("Finding by Name + Authors")
        query = queries.FIND_BOOK_BY_NAME_AND_AUTHORS
        vars = {"title": name, "authors": authors}
        return self._execute(query, vars, timeout)
