import sys
import pytest
import os
from unittest.mock import MagicMock
from graphql.client import GraphQLClient


def pytest_configure(config):
    setattr(
        sys,
        "extensions_location",
        os.getenv("CALIBRE_EXTENSIONS_PATH"),
    )
    setattr(sys, "resources_location", os.getenv("CALIBRE_RESOURCES_PATH"))


def pytest_unconfigure(config):
    delattr(sys, "extensions_location")
    delattr(sys, "resources_location")


@pytest.fixture
def mock_source():
    return MagicMock()


@pytest.fixture
def mock_gql_client():
    return MagicMock(spec=GraphQLClient)()
