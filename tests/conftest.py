"""Pytest 配置和共享 fixtures."""

import pytest


@pytest.fixture
def sample_config() -> dict[str, str]:
    """示例配置."""
    return {"key": "value", "debug": "true"}
