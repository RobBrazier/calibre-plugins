from logging import Logger  # noqa: F401
from typing import Callable, List, Optional
from pyjarowinkler import distance

from graphql.client import GraphQLClient

from . import queries
from .models import Book, Edition, map_from_book_query, map_from_edition_query

try:
    from calibre.utils.logging import Log  # noqa: F401
except ImportError:
    pass
except AttributeError:
    pass


class HardcoverIdentifier:
    def __init__(
        self,
        client: GraphQLClient,
        log,  # type: (Union[Log, Logger])
        identifier: str,
        api_key: str,
        match_sensitivity: float,
        timeout=30,
    ) -> None:
        self.log = log
        self.client = client
        self.client.set_token(api_key)
        self.identifier = identifier
        self.match_sensitivity = match_sensitivity
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
            author = None
            if authors:
                author = authors[0]
            book_ids = self.search_book(title, author)
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
        # Join authors and remove spaces
        return ",".join(sorted(book.authors))

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
            similarity = distance.get_jaro_distance(
                sanitized_query, sanitized_book_comparison
            )
            print(similarity)
            if similarity < self.match_sensitivity:
                self.log.info(f"Dropping {book_comparison} as it's too distant")
                continue
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

    def find_matching_edition(self, editions: list[Edition]):
        # TODO: do some actual matching here ...
        if len(editions) > 0:
            return editions[0]

    def _execute_internal(self, query: str, variables: Optional[dict] = None) -> dict:
        result = self.client.execute(query, variables, self.timeout)
        return result

    def _execute(self, query: str, variables: Optional[dict] = None) -> List[Book]:
        res = self._execute_internal(query, variables)
        result: List[Book] = []
        key = list(res.keys())[0]

        entries = res.get(key) if isinstance(res.get(key), list) else [res.get(key)]
        for entry in entries:
            if key == "books":
                result.append(map_from_book_query(entry))
            elif key in ["editions", "editions_by_pk"]:
                result.append(map_from_edition_query(entry))
        return result

    def search_book(self, name: str, author: str) -> list[int]:
        self.log.info("Searching for ids by Name")
        query = name
        if author:
            query += f" {author}"
        variables = {"query": query}
        search = self._execute_internal(queries.SEARCH_BY_NAME, variables)
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
        query = queries.FIND_BOOKS_BY_IDS % (queries.BOOK_DATA, queries.EDITION_DATA)
        variables = {"ids": book_ids}
        return self._execute(query, variables)

    def get_book_by_isbn_asin(self, isbn: str, asin: str) -> list[Book]:
        self.log.info("Finding by ISBN / ASIN")
        query = queries.FIND_BOOK_BY_ISBN_OR_ASIN % (
            queries.EDITION_DATA,
            queries.BOOK_DATA,
        )
        variables = {"isbn": isbn, "asin": asin}
        return self._execute(query, variables)

    def get_book_by_slug(self, slug: str) -> list[Book]:
        self.log.info("Finding by Slug")
        query = queries.FIND_BOOK_BY_SLUG % (queries.BOOK_DATA, queries.EDITION_DATA)
        variables = {"slug": slug}
        return self._execute(query, variables)

    def get_book_by_edition(self, edition: str) -> list[Book]:
        self.log.info("Finding by Edition ID")
        query = queries.FIND_BOOK_BY_EDITION % (queries.EDITION_DATA, queries.BOOK_DATA)
        variables = {"edition": edition}
        return self._execute(query, variables)
