"""Pytest configuration for stock_query tests."""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test requiring network"
    )
