"""Pytest configuration and fixtures."""

import pytest
import os
from unittest.mock import patch
from policy_enforcer.state import reset_state


@pytest.fixture(autouse=True)
def reset_state_fixture():
    """Automatically reset state before each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def mock_openai_key():
    """Provide a mock OpenAI API key for testing."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key-for-testing'}):
        yield 'test-api-key-for-testing'


@pytest.fixture
def no_api_key():
    """Remove API key from environment for testing."""
    original_keys = {
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY'),
    }
    
    # Remove all API keys
    for key in original_keys:
        if key in os.environ:
            del os.environ[key]
    
    yield
    
    # Restore original keys
    for key, value in original_keys.items():
        if value is not None:
            os.environ[key] = value


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that test individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that test component interactions"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that may take longer to run"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require real API keys"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests with slow marker or long-running patterns
        if (item.get_closest_marker("slow") or 
            "scenario" in item.name.lower() or
            "full" in item.name.lower()):
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """Setup function run before each test."""
    # Skip API tests if no real API key is available and not mocked
    if item.get_closest_marker("requires_api"):
        if not os.environ.get('OPENAI_API_KEY'):
            pytest.skip("Test requires OPENAI_API_KEY environment variable")


# Test data fixtures
@pytest.fixture
def sample_inventory():
    """Provide sample inventory data."""
    return ["TV", "Xbox", "Hiking Boots"]


@pytest.fixture
def sample_activities():
    """Provide sample activity data."""
    return ["Play games", "Go Camping", "Swimming"]