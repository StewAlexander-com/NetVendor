"""Pytest configuration for NetVendor tests."""

import os
import tempfile
import pytest

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up a clean test environment for each test."""
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set environment variables
        os.environ["NETVENDOR_DATA_DIR"] = tmpdir
        os.environ["NETVENDOR_OUTPUT_DIR"] = os.path.join(tmpdir, "output")
        
        # Create output directory
        os.makedirs(os.environ["NETVENDOR_OUTPUT_DIR"], exist_ok=True)
        
        yield
        
        # Clean up is handled automatically by tempfile.TemporaryDirectory

@pytest.fixture
def sample_mac_addresses():
    """Provide a list of sample MAC addresses for testing."""
    return [
        "00:11:22:33:44:55",
        "00-11-22-33-44-55",
        "001122334455",
        "0011.2233.4455",
        "invalid_mac",
        "00:11:22:33:44:GG"
    ]

@pytest.fixture
def sample_device_data():
    """Provide sample device data for testing."""
    return {
        "00:11:22:33:44:55": {
            "vlan": "1",
            "port": "Gi1/0/1",
            "vendor": "Vendor A"
        },
        "00:22:33:44:55:66": {
            "vlan": "2",
            "port": "Gi1/0/2",
            "vendor": "Vendor B"
        },
        "00:33:44:55:66:77": {
            "vlan": "1",
            "port": "Gi1/0/3",
            "vendor": "Vendor A"
        }
    }

@pytest.fixture
def sample_vendor_cache():
    """Provide sample vendor cache data for testing."""
    return {
        "001122": "Vendor A",
        "002233": "Vendor B",
        "003344": "Vendor C"
    }

@pytest.fixture
def sample_input_file(tmp_path):
    """Create a sample input file for testing."""
    file_path = tmp_path / "test_input.txt"
    content = """
Vlan    Mac Address       Type        Ports
----    -----------       ----        -----
1       0011.2233.4455   DYNAMIC     Gi1/0/1
2       0022.3344.5566   DYNAMIC     Gi1/0/2
1       0033.4455.6677   DYNAMIC     Gi1/0/3
"""
    file_path.write_text(content)
    return str(file_path) 