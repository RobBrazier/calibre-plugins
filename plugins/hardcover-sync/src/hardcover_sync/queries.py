SEARCH_BY_NAME = """
query Search($query: String!) {
  search(query: $query, query_type: "Book", per_page: 50) {
    results
  }
}
"""

EDITION_DATA = """
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
description
"""
BOOK_DATA = """
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
"""

FIND_BOOK_BY_SLUG = """
query FindBookBySlug($slug: String) {
  books(
    where: {slug: {_eq: $slug}}
  ) {
    %s
    editions(
      where: {reading_format_id: {_in: [1, 4]}}
      order_by: {users_count: desc_nulls_last, language_id: desc_nulls_last}
    ) {
      %s
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
    %s
    book {
      %s
    }
  }
}
"""

FIND_BOOK_BY_EDITION = """
query FindBookByEdition($edition: Int!) {
  editions_by_pk(id: $edition) {
    %s
    book {
      %s
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
    %s
    editions(
      where: {reading_format_id: {_in: [1, 4]}}
      order_by: {users_count: desc_nulls_last, language_id: desc_nulls_last}
    ) {
      %s
    }
  }
}
"""
