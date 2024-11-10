# pyright: reportIncompatibleMethodOverride=false
from multiprocessing.pool import ThreadPool
import os
import sys
from typing import Tuple, List
from calibre.ebooks.metadata.sources.base import Source
from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.config import OptionParser
import calibre.utils.logging as calibre_logging
from calibre import setup_cli_handlers
import logging
import threading
import re
from queue import Queue, Empty
from functools import partial

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

    API_URL = "https://api.hardcover.app/v1/graphql"

    def __init__(self, *args, **kwargs):
        Source.__init__(self, *args, **kwargs)
        sys.path.append(os.path.join(os.path.dirname(__file__), "deps"))
        from common.graphql import GraphQLClient
        from common.api_config import init_prefs

        self.config = init_prefs(self.ID_NAME)

        self.client = GraphQLClient(self.API_URL)
        self._qlock = threading.RLock()

    def is_configured(self):
        from common.api_config import get_option, API_KEY

        return bool(get_option(self.prefs, API_KEY))

    def config_widget(self):
        from common.api_config import APIConfigWidget

        return APIConfigWidget(self.prefs)

    def _execute(self, query, variables=None, timeout=30):
        from common.api_config import get_option, API_KEY

        if not self.client.token:
            self.client.set_token(get_option(self.prefs, API_KEY))

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
        def option_parser():
            "Parse command line options"
            parser = OptionParser(usage="Hardcover [t:title] [a:authors] [i:id]")
            parser.add_option(
                "--verbose", "-v", default=False, action="store_true", dest="verbose"
            )
            parser.add_option(
                "--debug_api", default=False, action="store_true", dest="debug_api"
            )
            return parser

        opts, args = option_parser().parse_args(args)
        if opts.debug_api:
            calibre_logging.default_log = calibre_logging.Log(
                level=calibre_logging.DEBUG
            )
        if opts.verbose:
            level = "DEBUG"
        else:
            level = "INFO"
        setup_cli_handlers(logging.getLogger("comicvine"), getattr(logging, level))
        log = calibre_logging.ThreadSafeLog(level=getattr(calibre_logging, level))
        (title, authors, ids) = (None, [], {})
        for arg in args:
            if arg.startswith("t:"):
                title = arg.split(":", 1)[1]
            if arg.startswith("a:"):
                authors.append(arg.split(":", 1)[1])
                authors = [a.strip() for a in re.split(",|&", authors[0])]
            if arg.startswith("i:"):
                (idtype, identifier) = arg.split(":", 2)[1:]
                ids[idtype] = identifier

        result_queue = Queue()
        self.identify(
            log, result_queue, False, title=title, authors=authors, identifiers=ids
        )
        ranking = self.identify_results_keygen(title, authors, ids)
        for rank, result in enumerate(sorted(result_queue.queue, key=ranking), start=1):
            self._print_result(result, rank)

    def _print_result(self, result, ranking):
        if result.pubdate:
            pubdate = str(result.pubdate.date())
        else:
            pubdate = "Unknown"
        result_text = "(%d) - %s: %s [%s]" % (
            ranking,
            result.identifiers[self.ID_NAME],
            result.title,
            pubdate,
        )
        print(result_text)

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
        shutdown = threading.Event()

        found_exact = False
        candidate_books = []

        # Exact match with a Hardcover Edition ID
        if hardcover_edition:
            books = self.get_book_by_edition(hardcover_edition, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Exact match with a Hardcover ID
        if hardcover_id:
            books = self.get_book_by_slug(hardcover_id, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Exact match with an ISBN or ASIN
        if (isbn or asin) and not found_exact:
            books = self.get_book_by_isbn_asin(isbn, asin, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Search for an Exact match by Fuzzy Title and Authors
        # NOTE: not sure about this one - it could mean that there are no meaningful results returned
        #       but should continue if nothing is returned
        if title and authors and not found_exact:
            books = self.get_book_by_name_authors(title, authors, timeout)
            if len(books) > 0:
                candidate_books = books
                found_exact = True

        # Fuzzy Search by Title
        if title and not found_exact:
            books = self.get_book_by_name(title, timeout)

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

        pool = ThreadPool(8)
        enqueue = partial(self.enqueue, log, result_queue, shutdown)
        try:
            pool.map(enqueue, [book for book in candidate_books])
        finally:
            shutdown.set()
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
            return None
        title = matching_edition.title
        authors = [c.author.name for c in matching_edition.contributions]
        meta = Metadata(title, authors)
        book_series = book.book_series
        if len(book_series) > 0:
            series = book_series[0]
            meta.series = series.series.name
            if series.position != 0:
                meta.series_index = series.position  # pyright: ignore
        meta.set_identifier("hardcover", book.slug)
        meta.set_identifier("hardcover-edition", str(matching_edition.id))
        if isbn := matching_edition.isbn_13:
            meta.set_identifier("isbn", isbn)
            self.cache_isbn_to_identifier(isbn, book.slug)
        if book.description:
            meta.comments = book.description
        if matching_edition.image and matching_edition.image.url:
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
                from datetime import datetime

                meta.pubdate = datetime.strptime(
                    matching_edition.release_date, "%Y-%m-%d"
                )
            except ValueError:
                log.warn("Unable to parse release date")
        if book.taggings:
            meta.tags = [tag.tag.tag for tag in book.taggings if tag.tag.tag]
        return meta

    def enqueue(self, log, result_queue, shutdown, book: Book):
        if shutdown.is_set():
            raise threading.ThreadError
        metadata = self.build_metadata(log, book)
        if metadata:
            self.clean_downloaded_metadata(metadata)
            with self._qlock:
                result_queue.put(metadata)
        log.info(f"Adding book slug '{book.slug}' to queue")

    def get_book_by_isbn_asin(self, isbn, asin, timeout=30) -> list[Book]:
        query = queries.FIND_BOOK_BY_ISBN_OR_ASIN
        vars = {"isbn": isbn, "asin": asin}
        return self._execute(query, vars, timeout)

    def get_book_by_slug(self, slug, timeout=30) -> list[Book]:
        query = queries.FIND_BOOK_BY_SLUG
        vars = {"slug": slug}
        return self._execute(query, vars, timeout)

    def get_book_by_edition(self, edition, timeout=30) -> list[Book]:
        query = queries.FIND_BOOK_BY_EDITION
        vars = {"edition": edition}
        return self._execute(query, vars, timeout)

    def get_book_by_name(self, name, timeout=30) -> list[Book]:
        query = queries.FIND_BOOK_BY_NAME
        vars = {"title": name}
        return self._execute(query, vars, timeout)

    def get_book_by_name_authors(self, name, authors, timeout=30) -> list[Book]:
        query = queries.FIND_BOOK_BY_NAME_AND_AUTHORS
        vars = {"title": name, "authors": authors}
        return self._execute(query, vars, timeout)
