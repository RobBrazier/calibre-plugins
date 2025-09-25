from typing import Callable, List, Optional, TypeVar
from pyjarowinkler import distance

from graphql.client import GraphQLClient

from . import queries
from .models import Book, Edition, map_from_book_query, map_from_edition_query

from calibre.utils.logging import Log

T = TypeVar("T", Book, Edition)

CONTRIBUTION_WEIGHTS = {"Author": 2.0}


class HardcoverIdentifier:
    def __init__(
        self,
        client: GraphQLClient,
        log: Log,
        identifier: str,
        api_key: str,
        match_sensitivity: float,
        languages: list[str],
        timeout=30,
    ) -> None:
        self.log = log
        self.client = client
        self.client.set_token(api_key)
        self.identifier = identifier
        self.match_sensitivity = match_sensitivity
        self.languages = self._validate_languages(languages)
        self.timeout = timeout

    def _validate_languages(self, languages: list[str]) -> list[str]:
        result = []
        for code in languages:
            if len(code) == 3:
                result.append(code)
            else:
                self.log.warn(
                    "Skipping invalid language code (expected len=3, got len=%d)",
                    code,
                    len(code),
                )
        if not result:
            self.log.warn("No languages specified - defaulting to eng")
            result.append("eng")

        return list(set(result))

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

        candidate_books: list[Book] = []

        # Exact match with a Hardcover Edition ID
        if hardcover_edition:
            candidate_books = self.get_book_by_edition(hardcover_edition)

        # Exact match with an ISBN or ASIN
        if (isbn or asin) and not candidate_books:
            candidate_books = self.get_book_by_isbn_asin(isbn, asin)

        # Exact match with a Hardcover ID
        if hardcover_id and not candidate_books:
            candidate_books = self.get_book_by_slug(hardcover_id)
            if len(candidate_books) > 0:
                candidate_books = self._filter_editions_by_title(candidate_books, title)

        # Fuzzy Search by Title
        if title and not candidate_books:
            author = None
            if authors:
                author = authors[0]
            book_ids = self.search_book(title, author)
            if len(book_ids) == 0:
                self.log.warn(f"No books found for {title=}, {author=}")
                return []
            books = self.get_books_by_ids(book_ids)

            # Get closest books by Title
            candidate_books = self._order_by_similarity(
                books, title, lambda book: book.title
            )

            candidate_books = self._filter_editions_by_title(candidate_books, title)

        # Filter by Authors
        if authors and candidate_books:
            candidate_books = self._filter_editions_by_author(candidate_books, authors)

        books = []
        for book in candidate_books:
            edition = self.find_matching_edition(book.editions)
            self.log.info(f"Matched {book.slug=} to {edition=}")
            if edition:
                book.editions = [edition]
                books.append(book)

        return books

    def _filter_editions_by_title(
        self, books: list[Book], title: Optional[str]
    ) -> list[Book]:
        for book in books:
            if not title:
                title = book.title
            editions = self._order_by_similarity(
                book.editions, title, lambda edition: edition.title, top_n=20
            )
            book.editions = editions
        # Remove books that now have no editions
        return [book for book in books if len(book.editions) > 0]

    def _filter_editions_by_author(
        self, books: list[Book], authors: list[str]
    ) -> list[Book]:
        top_n = 10
        for book in books:
            candidates: list[tuple[float, Edition]] = []
            for edition in book.editions:
                self.log.debug("filtering edition", edition)
                edition_authors = edition.authors
                total_similarity = 0.0
                for edition_author in edition_authors:
                    weight = CONTRIBUTION_WEIGHTS.get(edition_author.contribution, 1.0)
                    max_similarity = max(
                        [
                            distance.get_jaro_winkler_similarity(
                                edition_author.name,
                                author,
                                ignore_case=True,
                                scaling=0.0,
                            )
                            for author in authors
                        ]
                    )
                    weighted_similarity = max_similarity * weight
                    self.log.debug(
                        f"weighted similarity between {authors} and {edition_author}: {weighted_similarity}"
                    )
                    total_similarity += weighted_similarity
                similarity = 0.0
                if edition_authors:
                    similarity = total_similarity / len(edition_authors)
                self.log.debug(
                    f"overall similarity for {edition.title} ({edition.id}): {similarity}"
                )
                if similarity < self.match_sensitivity:
                    self.log.debug(
                        f"Dropping {edition.title} ({edition.id}) as it's too distant - similarity: {similarity}"
                    )
                    continue
                candidates.append((similarity, edition))
            candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
            if len(candidates) > top_n and top_n > 0:
                candidates = candidates[:top_n]
            editions = [item[1] for item in candidates]
            book.editions = editions
        # Remove books that now have no editions
        return [book for book in books if len(book.editions) > 0]

    def _filter_editions(
        self,
        books: list[Book],
        search: str | Callable[[Book], str],
        fn: Callable[[Edition], Optional[str]],
        top_n=20,
    ) -> list[Book]:
        for book in books:
            if callable(search):
                query = search(book)
            else:
                query = search
            editions = self._order_by_similarity(book.editions, query, fn, top_n)
            book.editions = editions

        # Remove books that now have no editions
        books = [book for book in books if len(book.editions) > 0]
        return books

    def _order_by_similarity(
        self,
        items: list[T],
        query: str,
        search_fn: Callable[[T], Optional[str]],
        top_n=20,
    ) -> list[T]:
        candidates: list[tuple[float, T]] = []
        for item in items:
            item_comparison = search_fn(item)
            if not item_comparison:
                continue
            try:
                identifier = f"book:{item.slug}"  # pyright: ignore[reportAttributeAccessIssue]
            except AttributeError:
                identifier = f"edition:{item.id}"
            self.log.debug(f"Comparing {query} to {item_comparison} ({identifier})")
            similarity = distance.get_jaro_winkler_similarity(query, item_comparison)
            if similarity < self.match_sensitivity:
                self.log.debug(
                    f"Dropping {item_comparison} ({identifier}) as it's too distant"
                )
                continue
            candidates.append((similarity, item))
        candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
        if len(candidates) > top_n and top_n > 0:
            candidates = candidates[:top_n]
        return [item[1] for item in candidates]

    def find_matching_edition(self, editions: list[Edition]) -> Optional[Edition]:
        sorted_editions = sorted(editions, key=lambda e: e.users_count, reverse=True)
        # Get the most 'popular' remaining edition
        if sorted_editions:
            return sorted_editions[0]
        return None

    def _execute_internal(self, query: str, variables: Optional[dict] = None) -> dict:
        query_with_fragments = f"{queries.FRAGMENTS}{query}"
        result = self.client.execute(query_with_fragments, variables, self.timeout)
        return result

    def _execute(self, query: str, variables: Optional[dict] = None) -> List[Book]:
        res = self._execute_internal(query, variables)
        result: List[Book] = []
        key = list(res.keys())[0]

        entries = res.get(key, []) if isinstance(res.get(key), list) else [res.get(key)]
        for entry in entries:
            if key == "books":
                result.append(map_from_book_query(entry))
            elif key in ["editions", "editions_by_pk"]:
                result.append(map_from_edition_query(entry))
        return result

    def search_book(self, name: str, author: Optional[str]) -> list[int]:
        query = name
        if author:
            query += f" {author}"
        self.log.info("Searching for ids by Name", query)
        variables = {"query": query}
        search = self._execute_internal(queries.SEARCH_BY_NAME, variables)
        ids = search.get("search", {}).get("ids", [])
        results = []
        for book_id in ids:
            try:
                results.append(int(book_id))
            except ValueError:
                self.log.error(f"Unable to parse book id {book_id} for {name}")
        self.log.info(f"Found {results=} for {query=}")
        return results

    def get_books_by_ids(self, book_ids: list[int]) -> list[Book]:
        self.log.info("Finding by book id", book_ids)
        variables = {"ids": book_ids, "languages": self.languages}
        return self._execute(queries.FIND_BOOKS_BY_IDS, variables)

    def get_book_by_isbn_asin(self, isbn: str, asin: str) -> list[Book]:
        self.log.info(f"Finding by ISBN / ASIN {isbn=} {asin=}")
        variables = {"isbn": isbn, "asin": asin}
        return self._execute(queries.FIND_BOOK_BY_ISBN_OR_ASIN, variables)

    def get_book_by_slug(self, slug: str) -> list[Book]:
        self.log.info("Finding by Slug", slug)
        variables = {"slug": slug, "languages": self.languages}
        books = self._execute(queries.FIND_BOOK_BY_SLUG, variables)
        result = []
        deduped_ids = []
        book_ids = [book.id for book in books]
        for book in books:
            canonical_id = book.canonical_id
            if canonical_id:
                if canonical_id not in book_ids:
                    deduped_ids.append(canonical_id)
                continue
            result.append(book)
        if deduped_ids:
            deduped_books = self.get_books_by_ids(deduped_ids)
            result += deduped_books
        return result

    def get_book_by_edition(self, edition: str) -> list[Book]:
        self.log.info("Finding by Edition ID", edition)
        variables = {"edition": edition}
        return self._execute(queries.FIND_BOOK_BY_EDITION, variables)
