#!/usr/bin/env python3
"""
Module for handling output generation in the NetVendor package.
This module provides functions for creating various output files:
- CSV files with device information
- Port-based reports
- Vendor distribution visualizations
- Text summaries of vendor distributions
"""

import os
import csv
import json
import plotly.graph_objects as go
from typing import Dict, List, Set, Any
from collections import Counter

def make_csv(device_data: List[Dict[str, str]], output_file: str) -> None:
    """
    Create a CSV file with device information.
    
    Args:
        device_data (List[Dict[str, str]]): List of device dictionaries
        output_file (str): Path to output CSV file
    """
    if not device_data:
        device_data = []
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        for device in device_data:
            writer.writerow([
                device.get('mac', ''),
                device.get('vendor', ''),
                device.get('vlan', ''),
                device.get('port', '')
            ])

def generate_port_report(device_data: List[Dict[str, str]], output_file: str, is_mac_table: bool = True) -> None:
    """
    Generate a CSV report with port-based device information.
    
    Args:
        device_data (List[Dict[str, str]]): List of device dictionaries
        output_file (str): Path to output CSV file
        is_mac_table (bool): Whether the data is from a MAC table
    """
    if not device_data:
        device_data = []
        
    # Group devices by port
    port_data = {}
    for device in device_data:
        port = device.get('port', '')
        if port not in port_data:
            port_data[port] = {
                'total_devices': 0,
                'vlans': set(),
                'vendors': set(),
                'devices': []
            }
        
        port_info = port_data[port]
        port_info['total_devices'] += 1
        port_info['vlans'].add(device.get('vlan', ''))
        port_info['vendors'].add(device.get('vendor', 'Unknown'))
        port_info['devices'].append(device)
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Port', 'Total Devices', 'VLANs', 'Vendors', 'Devices'])
        for port, info in port_data.items():
            writer.writerow([
                port,
                info['total_devices'],
                ','.join(sorted(info['vlans'])),
                ','.join(sorted(info['vendors'])),
                len(info['devices'])
            ])

def create_vendor_distribution(device_data: List[Dict[str, str]], output_file: str) -> None:
    """
    Create interactive visualizations of vendor and VLAN distributions.
    
    Args:
        device_data (List[Dict[str, str]]): List of device dictionaries
        output_file (str): Path to output HTML file
    """
    if not device_data:
        device_data = []
        
    # Count vendors
    vendor_counts = Counter(device.get('vendor', 'Unknown') for device in device_data)
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(vendor_counts.keys()),
        values=list(vendor_counts.values()),
        hole=.3
    )])
    
    # Update layout
    fig.update_layout(
        title='Vendor Distribution',
        annotations=[dict(text='Devices', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save to HTML
    fig.write_html(output_file)

def save_vendor_summary(device_data: List[Dict[str, str]], output_file: str) -> None:
    """
    Create a plain text summary of vendor distribution.
    
    Args:
        device_data (List[Dict[str, str]]): List of device dictionaries
        output_file (str): Path to output text file
    """
    if not device_data:
        device_data = []
        
    # Count vendors, using 'Unknown' for None or empty values
    vendor_counts = Counter(
        device.get('vendor', 'Unknown') if device.get('vendor') else 'Unknown'
        for device in device_data
    )
    total_devices = sum(vendor_counts.values()) or 1  # Avoid division by zero
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write summary
    with open(output_file, 'w') as f:
        f.write('Network Device Vendor Summary\n')
        f.write('+------------+-------+------------+\n')
        f.write('| Vendor       | Count | Percentage |\n')
        f.write('+============+=======+============+\n')
        
        for vendor, count in vendor_counts.most_common():
            percentage = (count / total_devices) * 100
            vendor_str = str(vendor) if vendor else 'Unknown'
            f.write(f'| {vendor_str:<12} | {count:<5} | {percentage:>6.1f}      % |\n') 