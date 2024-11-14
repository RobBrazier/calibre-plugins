import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))


def pytest_configure(config):
    import sys

    setattr(sys, "_called_from_test", True)


def pytest_unconfigure(config):
    delattr(sys, "_called_from_test")
