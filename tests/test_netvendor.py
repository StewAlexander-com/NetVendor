"""Tests for the NetVendor package."""

import os
import tempfile
from pathlib import Path
import pytest
from netvendor.core.oui_manager import OUIManager
from netvendor.utils.helpers import (
    is_mac_address,
    is_mac_address_table,
    parse_port_info,
    get_format_type
)

def test_is_mac_address():
    """Test MAC address validation."""
    assert is_mac_address("00:11:22:33:44:55")
    assert is_mac_address("00-11-22-33-44-55")
    assert is_mac_address("001122334455")
    assert is_mac_address("0011.2233.4455")
    assert not is_mac_address("00:11:22:33:44")  # Too short
    assert not is_mac_address("00:11:22:33:44:55:66")  # Too long
    assert not is_mac_address("00:11:22:33:44:GG")  # Invalid characters

def test_is_mac_address_table():
    """Test MAC address table detection."""
    assert is_mac_address_table("Vlan    Mac Address       Type        Ports")
    assert is_mac_address_table("VLAN ID  MAC Address      Port")
    assert not is_mac_address_table("Internet  10.0.0.1   1   0123.4567.89ab  ARPA")

def test_parse_port_info():
    """Test port information parsing."""
    assert parse_port_info("1       0001.0001.0001   DYNAMIC     Gi1/0/1") == "Gi1/0/1"
    assert parse_port_info("1        00:01:00:01:00:01 1") == "1"
    assert parse_port_info("No port info") is None

def test_get_format_type():
    """Test format type detection."""
    assert get_format_type("Vlan    Mac Address       Type        Ports") == "cisco"
    assert get_format_type("VLAN ID  MAC Address      Port") == "hp"
    assert get_format_type("Some other format") == "generic"

@pytest.fixture
def oui_manager():
    """Create a temporary OUI manager for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["NETVENDOR_DATA_DIR"] = tmpdir
        manager = OUIManager()
        yield manager

def test_oui_manager_cache(oui_manager):
    """Test OUI manager caching functionality."""
    # Test cache initialization
    assert isinstance(oui_manager.cache, dict)
    assert len(oui_manager.cache) == 0
    
    # Test vendor lookup and caching
    mac = "001122334455"
    vendor = oui_manager.get_vendor(mac)
    
    # Since we don't have a real API key, this should return None
    assert vendor is None
    
    # Test cache saving and loading
    oui_manager.save_cache(force=True)
    assert Path(oui_manager.cache_file).exists()
    
    # Create a new manager to test loading
    new_manager = OUIManager()
    assert isinstance(new_manager.cache, dict)

def test_oui_manager_failed_lookups(oui_manager):
    """Test OUI manager failed lookup tracking."""
    # Test failed lookup initialization
    assert isinstance(oui_manager.failed_lookups, set)
    assert len(oui_manager.failed_lookups) == 0
    
    # Test failed lookup tracking
    mac = "001122334455"
    vendor = oui_manager.get_vendor(mac)
    assert vendor is None
    assert mac in oui_manager.failed_lookups
    
    # Test failed lookup persistence
    oui_manager.save_failed_lookups()
    assert Path(oui_manager.failed_lookups_file).exists()
    
    # Create a new manager to test loading
    new_manager = OUIManager()
    assert isinstance(new_manager.failed_lookups, set)
    assert mac in new_manager.failed_lookups

def test_oui_manager_file_tracking(oui_manager):
    """Test OUI manager file tracking."""
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content")
        test_file = f.name
    
    # Test file metadata tracking
    metadata = oui_manager.get_file_metadata(test_file)
    assert isinstance(metadata, dict)
    assert "size" in metadata
    assert "mtime" in metadata
    assert "hash" in metadata
    
    # Test file change detection
    assert oui_manager.has_file_changed(test_file)
    oui_manager.update_file_metadata(test_file)
    assert not oui_manager.has_file_changed(test_file)
    
    # Clean up
    os.unlink(test_file) 