from typing import Callable, Optional

from . import queries
from .models import Book, Edition
from typing import Union  # noqa: F401
from logging import Logger  # noqa: F401

try:
    from calibre.utils.logging import Log  # noqa: F401
except ImportError:
    pass
except AttributeError:
    pass


class HardcoverIdentifier:
    API_URL = "https://api.hardcover.app/v1/graphql"

    def __init__(self, log, identifier: str, api_key: str, timeout=30) -> None:
        # type: (Union[Log, Logger], str, str, int) -> None
        from common.graphql import GraphQLClient

        self.log = log
        self.client = GraphQLClient(self.API_URL)
        self.client.set_token(api_key)
        self.identifier = identifier
        self.timeout = timeout

    def identify(
        self,
        title: Optional[str],
        authors: Optional[list[str]],
        identifiers: dict[str, str],
    ):
        hardcover_id = identifiers.get(self.identifier, None)
        hardcover_edition = identifiers.get(f"{self.identifier}-edition", None)
        isbn = identifiers.get("isbn", "")
        asin = identifiers.get("mobi-asin", "")

        # Exact match with a Hardcover Edition ID
        if hardcover_edition:
            books = self.get_book_by_edition(hardcover_edition)
            if len(books) > 0:
                return books

        # Exact match with a Hardcover ID
        if hardcover_id:
            books = self.get_book_by_slug(hardcover_id)
            if len(books) > 0:
                return books

        # Exact match with an ISBN or ASIN
        if isbn or asin:
            books = self.get_book_by_isbn_asin(isbn, asin)
            if len(books) > 0:
                return books

        candidate_books: list[Book] = []

        # Fuzzy Search by Title
        if title:
            book_ids = self.search_book(title)
            if len(book_ids) == 0:
                return []
            books = self.get_books_by_ids(book_ids)

            # Get closest books by Title
            candidate_books = self._order_by_similarity(
                books, title, lambda book: book.title
            )

        # Filter by Authors
        # TODO: make this code better - need to prioritise exact author matches
        # currently `the-hobbit` disappears if queried with
        #   > title: The Hobbit, author: J. R. R. Tolkien
        # as that one also has an author of Christopher Tolkien
        if authors and candidate_books and False:
            # Join authors and remove spaces
            search_authors = ",".join(sorted(authors))

            candidate_books = self._order_by_similarity(
                candidate_books, search_authors, self._normalise_authors, top_n=10
            )

        # TODO: filter less relevant editions as well - maybe by language?
        # need to see if I can grab the calibre configured language
        return candidate_books

    def _normalise_authors(self, book: Book) -> Optional[str]:
        edition = self.find_matching_edition(book.editions)
        if not edition:
            return None
        authors = [author.author.name for author in edition.contributions]
        # Join authors and remove spaces
        return ",".join(sorted(authors))

    def _order_by_similarity(
        self,
        books: list[Book],
        query: str,
        search_fn: Callable[[Book], Optional[str]],
        top_n=20,
    ) -> list[Book]:
        candidates: list[tuple[int, Book]] = []
        for book in books:
            book_comparison = search_fn(book)
            if not book_comparison:
                continue
            sanitized_query = self._sanitize(query)
            sanitized_book_comparison = self._sanitize(book_comparison)
            self.log.info(f"Comparing {sanitized_query} to {sanitized_book_comparison}")
            similarity = self.levenshtein_distance(
                sanitized_query, sanitized_book_comparison
            )
            candidates.append((similarity, book))
        candidates = sorted(candidates, key=lambda x: x[0])
        if len(candidates) > top_n and top_n > 0:
            candidates = candidates[:top_n]
        return [book[1] for book in candidates]

    @staticmethod
    def _sanitize(raw_input: str) -> str:
        # remove whitespace around string
        result = raw_input.strip()
        # remove whitespace inside string
        result = result.replace(" ", "")
        # remove non-alphanumeric characters
        result = "".join(c for c in result if c.isalnum())
        return result

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

    def find_matching_edition(self, editions: list[Edition]):
        # TODO: do some actual matching here ...
        if len(editions) > 0:
            return editions[0]

    def _execute_internal(self, query: str, variables: Optional[dict] = None) -> dict:
        result = self.client.execute(query, variables, self.timeout)
        return result

    def _execute(self, query: str, variables: Optional[dict] = None) -> list[Book]:
        books = self._execute_internal(query, variables)
        result: list[Book] = []
        if "books" not in books:
            raise ValueError("Invalid response, no books")
        for entry in books.get("books", []):
            result.append(Book.from_dict(entry))
        return result

    def search_book(self, name: str) -> list[int]:
        self.log.info("Searching for ids by Name")
        query = queries.SEARCH_BY_NAME
        variables = {"query": name}
        search = self._execute_internal(query, variables)
        hits = search.get("search", {}).get("results", {}).get("hits", [])
        results = []
        for hit in hits:
            book_id = hit.get("document", {}).get("id", "")
            if book_id:
                try:
                    results.append(int(book_id))
                except ValueError:
                    self.log.error(f"Unable to parse book id {book_id} for {name}")
        return results

    def get_books_by_ids(self, book_ids: list[int]) -> list[Book]:
        self.log.info("Finding by book id")
        query = queries.FIND_BOOKS_BY_IDS
        variables = {"ids": book_ids}
        return self._execute(query, variables)

    def get_book_by_isbn_asin(self, isbn: str, asin: str) -> list[Book]:
        self.log.info("Finding by ISBN / ASIN")
        query = queries.FIND_BOOK_BY_ISBN_OR_ASIN
        variables = {"isbn": isbn, "asin": asin}
        return self._execute(query, variables)

    def get_book_by_slug(self, slug: str) -> list[Book]:
        self.log.info("Finding by Slug")
        query = queries.FIND_BOOK_BY_SLUG
        variables = {"slug": slug}
        return self._execute(query, variables)

    def get_book_by_edition(self, edition: str) -> list[Book]:
        self.log.info("Finding by Edition ID")
        query = queries.FIND_BOOK_BY_EDITION
        variables = {"edition": edition}
        return self._execute(query, variables)
