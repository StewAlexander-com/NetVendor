#!/usr/bin/env python3
"""
Test cases for the vendor_output_handler module.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from netvendor.utils.vendor_output_handler import (
    make_csv,
    generate_port_report,
    create_vendor_distribution,
    save_vendor_summary
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def sample_device_data():
    """Create sample device data for testing."""
    return [
        {
            'mac': '00:11:22:33:44:55',
            'vendor': 'Cisco',
            'vlan': '100',
            'port': 'Gi1/0/1'
        },
        {
            'mac': 'AA:BB:CC:DD:EE:FF',
            'vendor': 'HP',
            'vlan': '200',
            'port': 'Gi1/0/2'
        }
    ]

@pytest.fixture
def sample_port_data():
    """Create sample port data for testing."""
    return {
        'Gi1/0/1': {
            'total_devices': 2,
            'vlans': {'100', '200'},
            'vendors': {'Cisco', 'HP'},
            'devices': [
                {
                    'mac': '00:11:22:33:44:55',
                    'vendor': 'Cisco',
                    'vlan': '100'
                },
                {
                    'mac': 'AA:BB:CC:DD:EE:FF',
                    'vendor': 'HP',
                    'vlan': '200'
                }
            ]
        }
    }

def test_make_csv(temp_output_dir, sample_device_data):
    """Test CSV file generation."""
    output_file = os.path.join(temp_output_dir, 'test-Devices.csv')
    make_csv(sample_device_data, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
        assert 'MAC,Vendor,VLAN,Port' in content
        assert '00:11:22:33:44:55,Cisco,100,Gi1/0/1' in content
        assert 'AA:BB:CC:DD:EE:FF,HP,200,Gi1/0/2' in content

def test_generate_port_report(temp_output_dir, sample_port_data):
    """Test port report generation."""
    output_file = os.path.join(temp_output_dir, 'test-Ports.csv')
    generate_port_report(sample_port_data, output_file, is_mac_table=True)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
        assert 'Port,Total Devices,VLANs,Vendors,Devices' in content
        assert 'Gi1/0/1,2,"100,200","Cisco,HP"' in content

def test_create_vendor_distribution(temp_output_dir, sample_device_data):
    """Test vendor distribution visualization creation."""
    output_file = os.path.join(temp_output_dir, 'vendor_distribution.html')
    create_vendor_distribution(sample_device_data, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
        assert 'plotly' in content
        assert 'Cisco' in content
        assert 'HP' in content

def test_save_vendor_summary(temp_output_dir, sample_device_data):
    """Test vendor summary text file generation."""
    output_file = os.path.join(temp_output_dir, 'vendor_summary.txt')
    save_vendor_summary(sample_device_data, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        content = f.read()
        assert 'Network Device Vendor Summary' in content
        assert 'Cisco' in content
        assert 'HP' in content
        assert '50.0' in content  # Percentage for each vendor

def test_empty_data_handling(temp_output_dir):
    """Test handling of empty data."""
    # Test empty device data
    output_file = os.path.join(temp_output_dir, 'empty-Devices.csv')
    make_csv([], output_file)
    assert os.path.exists(output_file)
    
    # Test empty port data
    output_file = os.path.join(temp_output_dir, 'empty-Ports.csv')
    generate_port_report({}, output_file, is_mac_table=True)
    assert os.path.exists(output_file)
    
    # Test empty vendor distribution
    output_file = os.path.join(temp_output_dir, 'empty-vendor_distribution.html')
    create_vendor_distribution([], output_file)
    assert os.path.exists(output_file)
    
    # Test empty vendor summary
    output_file = os.path.join(temp_output_dir, 'empty-vendor_summary.txt')
    save_vendor_summary([], output_file)
    assert os.path.exists(output_file)

def test_invalid_data_handling(temp_output_dir):
    """Test handling of invalid data."""
    invalid_data = [
        {
            'mac': 'invalid-mac',
            'vendor': None,
            'vlan': None,
            'port': None
        }
    ]
    
    # Test invalid device data
    output_file = os.path.join(temp_output_dir, 'invalid-Devices.csv')
    make_csv(invalid_data, output_file)
    assert os.path.exists(output_file)
    
    # Test invalid vendor distribution
    output_file = os.path.join(temp_output_dir, 'invalid-vendor_distribution.html')
    create_vendor_distribution(invalid_data, output_file)
    assert os.path.exists(output_file)
    
    # Test invalid vendor summary
    output_file = os.path.join(temp_output_dir, 'invalid-vendor_summary.txt')
    save_vendor_summary(invalid_data, output_file)
    assert os.path.exists(output_file) 