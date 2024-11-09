from typing import cast, TypeVar

T = TypeVar("T")


def safe_default(input: dict, key: str, defaultValue: T) -> T:
    if input.get(key):
        return cast(T, input.get(key))
    return defaultValue
