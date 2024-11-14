import sys

if not hasattr(sys, "_called_from_test"):
    from .source import Hardcover

    __all__ = ["Hardcover"]
