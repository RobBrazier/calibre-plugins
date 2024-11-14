import sys
import os
import pytest
from unittest.mock import MagicMock
from common.graphql import GraphQLClient

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))


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
