import json
import pytest
from unittest.mock import patch
from graphql.client import GraphQLClient

ENDPOINT = "https://test.endpoint/graphql"


@pytest.fixture
def client():
    yield GraphQLClient(ENDPOINT)


@patch("urllib.request.urlopen")
def test_execute_no_token(urlopen, client: GraphQLClient):
    query = """
query TestQuery($test: String) {
    test(test: $test) {
        results
    }
}
"""
    vars = {"test": "foo"}
    response = json.dumps({"data": {"test": "foo"}}).encode("utf-8")
    request_body = json.dumps({"query": query, "variables": vars}).encode("utf-8")

    urlopen.return_value.__enter__.return_value.read.return_value = response

    client.execute(query, vars)
    (request,), _ = urlopen.call_args
    assert request.full_url == ENDPOINT
    assert request.data == request_body
    assert "Authorization" not in request.headers
