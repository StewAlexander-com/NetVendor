"""Tests for the OUI Manager module."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from oui_manager import OUIManager

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def oui_manager(temp_data_dir, monkeypatch):
    """Create an OUIManager instance with a temporary data directory."""
    def mock_init(self):
        self.output_dir = temp_data_dir
        self.data_dir = temp_data_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.oui_file = self.data_dir / "oui_database.json"
        self.vendors = {
            "HP": ["Hewlett Packard", "HP Enterprise", "HP Inc"],
            "Apple": ["Apple, Inc"],
            "Dell": ["Dell Inc", "Dell Technologies"],
            "Cisco": ["Cisco Systems", "Cisco SPVTG"],
            "Mitel": ["Mitel Networks"],
        }
    
    monkeypatch.setattr(OUIManager, "__init__", mock_init)
    return OUIManager()

def test_load_database_empty(oui_manager):
    """Test loading database when file doesn't exist."""
    database = oui_manager.load_database()
    assert "last_updated" in database
    assert "vendors" in database
    assert all(vendor in database["vendors"] for vendor in oui_manager.vendors)
    assert all(isinstance(database["vendors"][vendor], list) for vendor in oui_manager.vendors)

def test_load_database_existing(oui_manager):
    """Test loading existing database."""
    test_data = {
        "last_updated": datetime.now().isoformat(),
        "vendors": {
            "HP": ["001122", "334455"],
            "Apple": ["AABBCC"],
            "Dell": [],
            "Cisco": ["DDEEFF"],
            "Mitel": []
        }
    }
    
    # Create test database file
    oui_manager.save_database(test_data)
    
    # Load and verify
    loaded_data = oui_manager.load_database()
    assert loaded_data == test_data

def test_save_database(oui_manager):
    """Test saving database."""
    test_data = {
        "last_updated": datetime.now().isoformat(),
        "vendors": {
            "HP": ["001122"],
            "Apple": ["AABBCC"],
            "Dell": [],
            "Cisco": ["DDEEFF"],
            "Mitel": []
        }
    }
    
    # Save test data
    oui_manager.save_database(test_data)
    
    # Read file directly and verify
    with open(oui_manager.oui_file, 'r') as f:
        saved_data = json.load(f)
    assert saved_data == test_data

def test_update_database(oui_manager, requests_mock):
    """Test database update functionality."""
    # Mock IEEE OUI database response
    mock_data = """
    00-11-22   (hex)        Hewlett Packard
    AA-BB-CC   (hex)        Apple, Inc
    DD-EE-FF   (hex)        Cisco Systems
    """
    requests_mock.get("http://standards-oui.ieee.org/oui/oui.txt", text=mock_data)
    
    # Update database
    assert oui_manager.update_database()
    
    # Verify database was updated
    database = oui_manager.load_database()
    assert "0011.22" in database["vendors"]["HP"]
    assert "aabb.cc" in database["vendors"]["Apple"]
    assert "ddee.ff" in database["vendors"]["Cisco"]

def test_check_update_needed_never_updated(oui_manager, monkeypatch):
    """Test update check when database has never been updated."""
    # Mock input to always return 'n'
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    
    database = oui_manager.load_database()
    assert database["last_updated"] == ""
    assert not oui_manager.check_update_needed()

def test_check_update_needed_recent(oui_manager, monkeypatch):
    """Test update check with recently updated database."""
    # Mock input to always return 'n'
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    
    # Create recently updated database
    test_data = {
        "last_updated": datetime.now().isoformat(),
        "vendors": {vendor: [] for vendor in oui_manager.vendors}
    }
    oui_manager.save_database(test_data)
    
    assert not oui_manager.check_update_needed()

def test_check_update_needed_old(oui_manager, monkeypatch):
    """Test update check with old database."""
    # Mock input to return 'y'
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    
    # Create old database (>30 days)
    old_date = (datetime.now() - timedelta(days=31)).isoformat()
    test_data = {
        "last_updated": old_date,
        "vendors": {vendor: [] for vendor in oui_manager.vendors}
    }
    oui_manager.save_database(test_data)
    
    assert oui_manager.check_update_needed()

def test_get_vendor_ouis(oui_manager):
    """Test retrieving vendor OUIs."""
    test_data = {
        "last_updated": datetime.now().isoformat(),
        "vendors": {
            "HP": ["001122", "334455"],
            "Apple": ["AABBCC"],
            "Dell": [],
            "Cisco": ["DDEEFF"],
            "Mitel": []
        }
    }
    oui_manager.save_database(test_data)
    
    # Test existing vendor
    hp_ouis = oui_manager.get_vendor_ouis("HP")
    assert isinstance(hp_ouis, set)
    assert "001122" in hp_ouis
    assert "334455" in hp_ouis
    
    # Test empty vendor
    dell_ouis = oui_manager.get_vendor_ouis("Dell")
    assert isinstance(dell_ouis, set)
    assert len(dell_ouis) == 0
    
    # Test non-existent vendor
    unknown_ouis = oui_manager.get_vendor_ouis("Unknown")
    assert isinstance(unknown_ouis, set)
    assert len(unknown_ouis) == 0 