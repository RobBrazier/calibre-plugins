FIND_BOOK_BY_NAME = """
query FindBookByName($title: String) {
  books(
    where: {title: {_iregex: $title}}
    order_by: {users_read_count: desc_nulls_last}
  ) {
    title
    slug
    book_series {
      series {
        name
      }
    }
    taggings(where: {spoiler: {_eq: false}}, limit: 10, distinct_on: tag_id) {
      tag {
        tag
      }
    }
    editions(
      where: {_or: [{edition_format: {_neq: "Audiobook"}}, {edition_format: {_is_null: true}}]}
      order_by: {users_count: desc_nulls_last}
    ) {
      id
      isbn_13
      title
      contributions {
        author {
          name
        }
      }
      image {
        url
      }
      language {
        code3
      }
      publisher {
        name
      }
      release_date
    }
    description
  }
}
"""

FIND_BOOK_BY_NAME_AND_AUTHORS = """
query FindBookByNameAndAuthors($title: String, $authors: [String!]) {
  books(
    where: {title: {_iregex: $title}, contributions: {author: {name: {_in: $authors}}}}
    order_by: {users_read_count: desc_nulls_last}
  ) {
    title
    slug
    book_series {
      series {
        name
      }
    }
    taggings(where: {spoiler: {_eq: false}}, limit: 10, distinct_on: tag_id) {
      tag {
        tag
      }
    }
    editions(
      where: {_or: [{edition_format: {_neq: "Audiobook"}}, {edition_format: {_is_null: true}}]}
      order_by: {users_count: desc_nulls_last}
    ) {
      id
      isbn_13
      title
      contributions {
        author {
          name
        }
      }
      image {
        url
      }
      language {
        code3
      }
      publisher {
        name
      }
      release_date
    }
    description
  }
}
"""

FIND_BOOK_BY_SLUG = """
query FindBookBySlug($slug: String) {
  books(
    where: {slug: {_eq: $slug}}
    order_by: {users_read_count: desc_nulls_last}
  ) {
    title
    slug
    book_series {
      series {
        name
      }
    }
    taggings(where: {spoiler: {_eq: false}}, limit: 10, distinct_on: tag_id) {
      tag {
        tag
      }
    }
    editions(
      where: {_or: [{edition_format: {_neq: "Audiobook"}}, {edition_format: {_is_null: true}}]}
      order_by: {users_count: desc_nulls_last}
    ) {
      id
      isbn_13
      title
      contributions {
        author {
          name
        }
      }
      image {
        url
      }
      language {
        code3
      }
      publisher {
        name
      }
      release_date
    }
    description
  }
}
"""

FIND_BOOK_BY_ISBN_OR_ASIN = """
query FindBookByIsbnOrAsin($isbn: String, $asin: String) {
  books(
    where: {editions: {_and: [{_or: [{isbn_13: {_eq: $isbn}}, {isbn_10: {_eq: $isbn}}, {asin: {_eq: $isbn}}, {asin: {_eq: $asin}}]}, {_or: [{edition_format: {_neq: "Audiobook"}}, {edition_format: {_is_null: true}}]}]}}
    order_by: {users_read_count: desc_nulls_last}
  ) {
    title
    slug
    book_series {
      series {
        name
      }
    }
    taggings(where: {spoiler: {_eq: false}}, limit: 10, distinct_on: tag_id) {
      tag {
        tag
      }
    }
    editions(
      where: {_and: [{_or: [{isbn_13: {_eq: $isbn}}, {isbn_10: {_eq: $isbn}}, {asin: {_eq: $isbn}}, {asin: {_eq: $asin}}]}, {_or: [{edition_format: {_neq: "Audiobook"}}, {edition_format: {_is_null: true}}]}]}
      order_by: {users_count: desc_nulls_last}
    ) {
      id
      isbn_13
      title
      contributions {
        author {
          name
        }
      }
      image {
        url
      }
      language {
        code3
      }
      publisher {
        name
      }
      release_date
    }
    description
  }
}
"""

FIND_BOOK_BY_EDITION = """
query FindBookByEdition($edition: Int) {
  books(
    where: {editions: {id: {_eq: $edition}}}
    order_by: {users_read_count: desc_nulls_last}
  ) {
    title
    slug
    book_series {
      series {
        name
      }
    }
    taggings(where: {spoiler: {_eq: false}}, limit: 10, distinct_on: tag_id) {
      tag {
        tag
      }
    }
    editions(
      where: {_or: [{edition_format: {_neq: "Audiobook"}}, {edition_format: {_is_null: true}}]}
      order_by: {users_count: desc_nulls_last}
    ) {
      id
      isbn_13
      title
      contributions {
        author {
          name
        }
      }
      image {
        url
      }
      language {
        code3
      }
      publisher {
        name
      }
      release_date
    }
    description
  }
}
"""
