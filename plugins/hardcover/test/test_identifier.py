from unittest.mock import call
from pathlib import Path
import json
import pytest

from hardcover import queries
from hardcover.identifier import HardcoverIdentifier
from .utils import create_book_response, create_edition
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)

FIXTURE_DIR = Path(__file__).parent.resolve() / "data"

EDITION_ID = "8548995"
SLUG = "the-hobbit"
ISBN = "9780618968633"
ASIN = "0007458428"


@pytest.fixture
def identifier(mock_gql_client, monkeypatch):
    identifier = HardcoverIdentifier(
        mock_gql_client, logger, "hardcover", "api_key", 0.7
    )
    return identifier


@pytest.mark.parametrize(
    "identifiers, query, variables",
    [
        pytest.param(
            {"hardcover-edition": EDITION_ID},
            queries.FIND_BOOK_BY_EDITION % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"edition": EDITION_ID},
            id="hardcover-edition",
        ),
        pytest.param(
            {"hardcover": SLUG},
            queries.FIND_BOOK_BY_SLUG % (queries.BOOK_DATA, queries.EDITION_DATA),
            {"slug": SLUG},
            id="hardcover-slug",
        ),
        pytest.param(
            {"isbn": ISBN},
            queries.FIND_BOOK_BY_ISBN_OR_ASIN
            % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"isbn": ISBN, "asin": ""},
            id="isbn",
        ),
        pytest.param(
            {"mobi-asin": ASIN},
            queries.FIND_BOOK_BY_ISBN_OR_ASIN
            % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"isbn": "", "asin": ASIN},
            id="asin",
        ),
        pytest.param(
            {"isbn": ISBN, "mobi-asin": ASIN},
            queries.FIND_BOOK_BY_ISBN_OR_ASIN
            % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"isbn": ISBN, "asin": ASIN},
            id="isbn+asin",
        ),
    ],
)
def test_identify_by_identifiers(
    identifiers, query, variables, identifier: HardcoverIdentifier, mock_gql_client
):
    title = "The Hobbit"
    authors = ["J. R. R. Tolkien"]

    data = create_book_response(
        title=title,
        slug=SLUG,
        editions=[
            create_edition(
                title=title,
                id=int(EDITION_ID),
                isbn="9780618968633",
                authors=authors,
                publisher="Houghton Mifflin Harcourt",
                release_date="1937-01-01",
            )
        ],
    )

    mock_gql_client.execute.return_value = data

    results = identifier.identify(title, authors, identifiers)

    assert len(results) == 1
    mock_gql_client.execute.assert_called_once_with(query, variables, 30)


@pytest.mark.parametrize(
    "identifiers, query, variables",
    [
        pytest.param(
            {"hardcover-edition": EDITION_ID},
            queries.FIND_BOOK_BY_EDITION % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"edition": EDITION_ID},
            id="hardcover-edition",
        ),
        pytest.param(
            {"hardcover": SLUG},
            queries.FIND_BOOK_BY_SLUG % (queries.BOOK_DATA, queries.EDITION_DATA),
            {"slug": SLUG},
            id="hardcover-slug",
        ),
        pytest.param(
            {"isbn": ISBN},
            queries.FIND_BOOK_BY_ISBN_OR_ASIN
            % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"isbn": ISBN, "asin": ""},
            id="isbn",
        ),
        pytest.param(
            {"mobi-asin": ASIN},
            queries.FIND_BOOK_BY_ISBN_OR_ASIN
            % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"isbn": "", "asin": ASIN},
            id="asin",
        ),
        pytest.param(
            {"isbn": ISBN, "mobi-asin": ASIN},
            queries.FIND_BOOK_BY_ISBN_OR_ASIN
            % (queries.EDITION_DATA, queries.BOOK_DATA),
            {"isbn": ISBN, "asin": ASIN},
            id="isbn+asin",
        ),
    ],
)
def test_identify_by_identifiers_no_results(
    identifiers, query, variables, identifier: HardcoverIdentifier, mock_gql_client
):
    mock_gql_client.execute.side_effect = [
        {"books": []},
        {"search": {"results": {"hits": []}}},
    ]

    results = identifier.identify("Title", ["Authors"], identifiers)

    assert len(results) == 0

    mock_gql_client.execute.assert_has_calls(
        [
            call(query, variables, 30),
            call(queries.SEARCH_BY_NAME, {"query": "Title Authors"}, 30),
        ]
    )


def test_identify_by_title_and_author(identifier: HardcoverIdentifier, mock_gql_client):
    title = "The Hobbit"
    authors = ["J.R.R. Tolkien", "Christopher Tolkien"]

    result_ids = [
        382700,
        377938,
        346073,
        189932,
        710182,
        485045,
        492009,
        124077,
        982529,
        253171,
        503279,
        551645,
        491273,
        859461,
        506520,
        820935,
        485044,
        679221,
        508399,
        21179,
        104966,
        131746,
        147014,
        132369,
        110661,
    ]
    search_results = {
        "search": {
            "results": {
                "hits": [{"document": {"id": str(book_id)}} for book_id in result_ids]
            }
        }
    }
    with open(FIXTURE_DIR / "find_books_by_id.json") as f:
        books_result = json.loads(f.read())
    mock_gql_client.execute.side_effect = [search_results, books_result["data"]]
    results = identifier.identify(title, authors, {})

    assert results[0].slug == "the-hobbit"

    mock_gql_client.execute.assert_has_calls(
        [
            call(queries.SEARCH_BY_NAME, {"query": f"{title} {authors[0]}"}, 30),
            call(
                queries.FIND_BOOKS_BY_IDS % (queries.BOOK_DATA, queries.EDITION_DATA),
                {"ids": result_ids},
                30,
            ),
        ]
    )


def test_identify_no_title(identifier: HardcoverIdentifier, mock_gql_client):
    results = identifier.identify(None, None, {})

    assert len(results) == 0

    assert not mock_gql_client.execute.called
