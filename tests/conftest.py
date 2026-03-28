"""
pytest configuration for Artificiall Ops Manager tests.
"""

import pytest
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "test_telegram_id": "999999999",
        "test_admin_id": "111111111",
        "test_ceo_id": "888888888",
        "test_employee_name": "Test Employee",
        "test_phone": "+5511999999999",
        "test_cargo": "Test Cargo",
    }
