SEARCH_BY_NAME = """
query Search($query: String!) {
  search(query: $query, query_type: "Book", per_page: 50) {
    results
  }
}
"""

FRAGMENTS = """
fragment EditionData on editions {
  title
  id
  isbn_13
  asin
  cached_contributors
  cached_image
  reading_format_id
  language {
    code3
  }
  publisher {
    name
  }
  release_date
}

fragment BookData on books {
  id
  title
  slug
  rating
  description
  book_series(where: {featured: {_eq: true}}) {
    series {
      name
    }
    position
  }
  cached_tags
  rating
}
"""

FIND_BOOK_BY_SLUG = """
query FindBookBySlug($slug: String) {
  books(
    where: {slug: {_eq: $slug}}
  ) {
    ...BookData
    editions(
      where: {reading_format_id: {_in: [1, 4]}}
      order_by: {users_count: desc_nulls_last, language_id: desc_nulls_last}
    ) {
      ...EditionData
    }
  }
}
"""

FIND_BOOK_BY_ISBN_OR_ASIN = """
query FindBookByIsbnOrAsin($isbn: String, $asin: String) {
  editions(
    where: {_and: [{_or: [{isbn_13: {_eq: $isbn}}, {isbn_10: {_eq: $isbn}}, {asin: {_eq: $asin}}]}, {reading_format_id: {_in: [1, 4]}}]}
    order_by: {users_count: desc_nulls_last}
  ) {
    ...EditionData
    book {
      ...BookData
    }
  }
}
"""

FIND_BOOK_BY_EDITION = """
query FindBookByEdition($edition: Int!) {
  editions_by_pk(id: $edition) {
    ...EditionData
    book {
      ...BookData
    }
  }
}
"""


FIND_BOOKS_BY_IDS = """
query FindBooksByIds($ids: [Int!]) {
  books(
    where: {id: {_in: $ids}}
    order_by: {users_read_count: desc_nulls_last}
  ) {
    ...BookData
    editions(
      where: {reading_format_id: {_in: [1, 4]}}
      order_by: {users_count: desc_nulls_last, language_id: desc_nulls_last}
    ) {
      ...EditionData
    }
  }
}
"""
