from common import utils
import pytest


@pytest.mark.parametrize(
    "key,value,present",
    [
        ("string", "value", True),
        ("string", "value", False),
        ("int", 1, True),
        ("int", 1, False),
        ("bool", True, True),
        ("bool", True, False),
        ("dict", {"foo": "bar"}, True),
        ("dict", {"foo": "bar"}, False),
    ],
)
def test_safe_default_present(key, value, present):
    input = {}
    if present:
        input = {key: value}
    assert utils.safe_default(input, key, value) == value
