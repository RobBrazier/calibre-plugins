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
from queue import Queue
from functools import partial

from ._version import __version_tuple__
from .models import Book


class Hardcover(Source):
    name = "Hardcover"
    description = "Downloads metadata and covers from Hardcover.app"
    author = "Rob Brazier"
    version = __version_tuple__
    minimum_calibre_version = (7, 7, 0)

    ID_NAME = "hardcover"

    capabilities = frozenset(["identify", "cover"])
    touched_fields = frozenset(
        ["title", "authors", f"identifier:{ID_NAME}", "pubdate", "series", "tags"]
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

    def _execute(self, query, variables=None):
        from common.api_config import get_option, API_KEY

        self.client.set_token(get_option(self.prefs, API_KEY))
        return self.client.execute(query, variables)

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
        isbn = identifiers.get("isbn", None)

        if hardcover_id:
            books = self.get_book_by_slug(hardcover_id)
            if len(books) > 0:
                self.enqueue(log, result_queue, threading.Event(), books[0])
                return None
        if title:
            books = self.get_book_by_name(title)

            candidate_books = books

            isbn_matching_books = []
            # Check if a book matches the given ISBN
            for book in books:
                if len(book.editions) == 0:
                    continue
                has_match = False
                for edition in book.editions:
                    if isbn == edition.isbn_13 or isbn == edition.isbn_10:
                        isbn_matching_books.append(book)
                        has_match = True
                        break
                if has_match:
                    break

            if len(isbn_matching_books) > 0:
                candidate_books = isbn_matching_books

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
            candidate_authors: List[Tuple[int, Book]] = []
            if authors:
                for book in candidate_books:
                    book_authors = [c.author.name for c in book.contributions]
                    similarity = self.similar_authors(authors, book_authors)
                    candidate_authors.append((similarity, book))
                candidate_authors = sorted(candidate_authors, key=lambda x: x[0])
                if len(candidate_authors) > 10:
                    candidate_authors = candidate_authors[:10]

                candidate_books = [book[1] for book in candidate_authors]

            pool = ThreadPool(16)
            shutdown = threading.Event()
            enqueue = partial(self.enqueue, log, result_queue, shutdown)
            try:
                pool.map(enqueue, [book for book in candidate_books])
            finally:
                shutdown.set()
        return None

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

    def build_metadata(self, log, book: Book):
        title = f"{book.title}"
        authors = [c.author.name for c in book.contributions]
        meta = Metadata(title, authors)
        if len(book.book_series) > 0:
            meta.series = book.book_series[0].series.name
            if index := book.book_series[0].position:
                meta.series_index = str(index)
        meta.set_identifier("hardcover", str(book.slug))
        if book.description:
            meta.comments = book.description
        if book.image:
            meta.has_cover = True
        else:
            meta.has_cover = False
        # if book.publisher:
        #     meta.publisher = book.publisher.name
        if book.release_date:
            try:
                from datetime import datetime

                meta.pubdate = datetime.strptime(book.release_date, "%Y-%m-%d")
            except ValueError:
                log.warn("Unable to parse release date")
        if book.taggings:
            meta.tags = [tag.tag.tag for tag in book.taggings if tag.tag.tag]
        return meta

    def enqueue(self, log, result_queue, shutdown, book: Book):
        if shutdown.is_set():
            raise threading.ThreadError
        slug = book.slug
        metadata = self.build_metadata(log, book)
        if metadata:
            self.clean_downloaded_metadata(metadata)
            with self._qlock:
                result_queue.put(metadata)
        log.info(f"Adding book slug '{slug}' to queue")

    def get_book_by_slug(self, slug) -> list[Book]:
        query = """
            query FindBookBySlug($slug: String) {
              books(
                where: {slug: {_eq: $slug}}
                order_by: {users_read_count: desc_nulls_last}
              ) {
                title
                slug
                users_read_count
                contributions {
                  author {
                    name
                  }
                }
                release_date
                book_series {
                  series {
                    name
                  }
                }
                taggings {
                  tag {
                    tag
                  }
                }
                image {
                  url
                }
                editions {
                  asin
                  isbn_13
                  isbn_10
                  title
                }
                description
              }
            }
            """
        vars = {"slug": slug}
        books = self._execute(query, vars)
        result = []
        if "books" in books:
            for entry in books.get("books", []):
                result.append(Book.from_dict(entry))
        return result

    def get_book_by_name(self, name) -> list[Book]:
        query = """
            query FindBookByName($title: String) {
              books(
                where: {title: {_regex: $title}}
                order_by: {users_read_count: desc_nulls_last}
              ) {
                title
                slug
                users_read_count
                contributions {
                  author {
                    name
                  }
                }
                release_date
                book_series {
                  series {
                    name
                  }
                }
                taggings {
                  tag {
                    tag
                  }
                }
                image {
                  url
                }
                editions {
                  asin
                  isbn_13
                  isbn_10
                  title
                }
                description
              }
            }
            """
        vars = {"title": name}
        books = self._execute(query, vars)
        result = []
        if "books" in books:
            for entry in books.get("books", []):
                result.append(Book.from_dict(entry))
        return result
