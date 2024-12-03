import sys
import pytest
from unittest.mock import MagicMock
from graphql.client import GraphQLClient


def pytest_configure(config):
    setattr(sys, "_called_from_test", True)


def pytest_unconfigure(config):
    delattr(sys, "_called_from_test")


@pytest.fixture
def mock_source():
    return MagicMock()


@pytest.fixture
def mock_gql_client():
    return MagicMock(spec=GraphQLClient)()
