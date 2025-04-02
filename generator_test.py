#!/usr/bin/env python3

"""
Generate test files for NetVendor testing:
1. Cisco MAC address table (500 entries)
2. Cisco show ip arp table (500 entries)
3. Simple MAC address list (100 entries)

Test files are stored in tests/data directory.
"""

import random
from pathlib import Path
import os
import shutil
from collections import Counter

# VENDORS dictionary with real OUIs
VENDORS = {
    'Cisco': [
        '00:00:0C', '00:01:42', '00:01:43', '00:01:63', '00:01:64',
        '00:0E:83', '00:0E:84', '00:1A:A0', '00:23:EB', '00:25:45',
        '58:AC:78', '68:99:CD', '70:DB:98', 'B4:A4:E3', 'FC:FB:FB'
    ],
    'HP': [
        '00:0B:CD', '00:0F:20', '00:11:0A', '00:1C:C4', '00:24:81',
        '00:25:B3', '00:30:C1', '00:60:B0', '08:00:09', '10:60:4B',
        '1C:C1:DE', '28:92:4A', '38:63:BB', '3C:D9:2B', '94:57:A5'
    ],
    'Dell': [
        '00:06:5B', '00:08:74', '00:0B:DB', '00:12:3F', '00:14:22',
        '00:15:C5', '00:1E:4F', '14:18:77', '18:A9:9B', '18:DB:F2',
        '24:B6:FD', '28:F1:0E', 'B8:AC:6F', 'F0:1F:AF', 'F8:DB:88'
    ],
    'Apple': [
        '00:03:93', '00:0A:27', '00:0A:95', '00:0D:93', '00:1B:63',
        '00:1E:52', '00:1F:5B', '00:1F:F3', '00:21:E9', '00:22:41',
        '00:23:12', '00:23:32', '00:23:6C', '00:23:DF', '00:24:36'
    ],
    'Mitel': [
        '00:90:7F', '08:00:0F', '00:00:8A', '00:10:96', '00:10:97',
        '00:10:98', '00:10:99', '00:10:9A', '00:10:9B', '00:10:9C'
    ],
    'Juniper': [
        '00:05:85', '00:12:1E', '00:19:E2', '00:23:9C', '00:26:88',
        '28:8A:1C', '28:C0:DA', '2C:21:72', '2C:6B:F5', '3C:61:04'
    ],
    'Aruba': [
        '00:0B:86', '00:1A:1E', '04:BD:88', '24:DE:C6', '40:E3:D6',
        '6C:F3:7F', '84:D4:7E', '94:B4:0F', 'AC:A3:1E', 'D8:C7:C8'
    ],
    'Extreme': [
        '00:01:30', '00:04:96', '00:0F:DB', '00:11:88', '00:12:CF',
        '00:13:65', '00:14:4F', '00:19:30', '00:1F:45', '00:21:58'
    ]
}

def setup_test_data_directory() -> Path:
    """
    Set up the tests/data directory.
    Creates fresh directory and adds .gitkeep
    """
    test_data_dir = Path('tests/data')
    
    # Remove existing test data directory if it exists
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create fresh test data directory
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep file
    (test_data_dir / '.gitkeep').touch()
    
    return test_data_dir

def generate_mac_suffix():
    """Generate random MAC address suffix"""
    return f"{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"

def generate_ip(index):
    """Generate IP address in 192.168.x.y format"""
    subnet = (index - 1) // 254 + 1
    host = ((index - 1) % 254) + 1
    return f"192.168.{subnet}.{host}"

def get_vendor_distribution(total_entries: int) -> dict:
    """Generate a realistic vendor distribution."""
    vendor_counts = {
        'Cisco': random.randint(int(total_entries * 0.18), int(total_entries * 0.22)),  # ~20%
        'HP': random.randint(int(total_entries * 0.14), int(total_entries * 0.18)),     # ~16%
        'Dell': random.randint(int(total_entries * 0.12), int(total_entries * 0.16)),   # ~14%
        'Apple': random.randint(int(total_entries * 0.10), int(total_entries * 0.14)),  # ~12%
        'Juniper': random.randint(int(total_entries * 0.08), int(total_entries * 0.12)), # ~10%
        'Aruba': random.randint(int(total_entries * 0.08), int(total_entries * 0.12)),   # ~10%
        'Extreme': random.randint(int(total_entries * 0.06), int(total_entries * 0.10)), # ~8%
        'Mitel': random.randint(int(total_entries * 0.06), int(total_entries * 0.10))    # ~8%
    }
    
    # Adjust to match total_entries exactly
    total = sum(vendor_counts.values())
    scale_factor = total_entries / total
    
    for vendor in vendor_counts:
        vendor_counts[vendor] = int(vendor_counts[vendor] * scale_factor)
    
    # Handle rounding errors
    total = sum(vendor_counts.values())
    if total < total_entries:
        vendor_counts['Cisco'] += total_entries - total
    elif total > total_entries:
        vendor_counts['Cisco'] -= total - total_entries
    
    return vendor_counts

def generate_mac_address_table(count: int) -> tuple[str, dict]:
    """
    Generate a Cisco MAC address table output.
    Matches format expected by is_mac_address_table() function.
    """
    header = "Vlan    Mac Address       Type        Ports\n"
    header += "----    -----------       ----        -----\n"
    entries = []
    vendor_counts = {}
    
    vendor_distribution = get_vendor_distribution(count)
    
    for vendor, count in vendor_distribution.items():
        for _ in range(count):
            oui = random.choice(VENDORS[vendor])
            mac_suffix = generate_mac_suffix()
            vlan = random.randint(1, 100)
            port = f"Gi1/0/{random.randint(1, 48)}"
            entry = f"{vlan:<8}{oui.replace(':', '.')}.{mac_suffix.replace(':', '')}   DYNAMIC     {port}"
            entries.append(entry)
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
    
    random.shuffle(entries)
    return header + "\n".join(entries), vendor_counts

def generate_arp_table(count: int) -> tuple[str, dict]:
    """
    Generate a Cisco show ip arp output.
    Matches format expected by core processing code.
    """
    header = "Protocol  Address          Age (min)  Hardware Addr   Type   Interface\n"
    entries = []
    vendor_counts = {}
    
    vendor_distribution = get_vendor_distribution(count)
    
    for vendor, count in vendor_distribution.items():
        for i in range(count):
            oui = random.choice(VENDORS[vendor])
            mac_suffix = generate_mac_suffix()
            ip = generate_ip(i + 1)
            vlan = random.randint(1, 100)
            entry = f"Internet  {ip:<15} {random.randint(0, 240):<10} {oui.replace(':', '.')}.{mac_suffix.replace(':', '')}  ARPA   Vlan{vlan}"
            entries.append(entry)
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
    
    random.shuffle(entries)
    return header + "\n".join(entries), vendor_counts

def generate_mac_list(count: int) -> tuple[str, dict]:
    """Generate a simple list of MAC addresses."""
    entries = []
    vendor_counts = {}
    
    vendor_distribution = get_vendor_distribution(count)
    
    for vendor, count in vendor_distribution.items():
        for _ in range(count):
            oui = random.choice(VENDORS[vendor])
            mac_suffix = generate_mac_suffix()
            entries.append(f"{oui}:{mac_suffix}")
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
    
    random.shuffle(entries)
    return "\n".join(entries), vendor_counts

def print_vendor_statistics(stats: dict, total: int, file_type: str):
    """Print vendor distribution statistics."""
    print(f"\n{file_type} Vendor Distribution:")
    print("-" * 50)
    for vendor, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"{vendor:8}: {count:3} entries ({percentage:5.1f}%)")
    print("-" * 50)

def write_test_file(content: str, filename: str, data_dir: Path) -> Path:
    """Write content to a test file and return its path."""
    file_path = data_dir / filename
    with open(file_path, 'w') as f:
        f.write(content)
    return file_path

def main():
    """Generate all test files in tests/data directory."""
    # Set up test data directory
    test_data_dir = setup_test_data_directory()
    print(f"Test data directory created: {test_data_dir}")
    
    # Generate MAC address table
    print("\nGenerating MAC address table...")
    mac_table_content, mac_table_stats = generate_mac_address_table(500)
    mac_table_path = write_test_file(mac_table_content, 'test-mac-table.txt', test_data_dir)
    print(f"Generated MAC address table -> {mac_table_path}")
    print_vendor_statistics(mac_table_stats, 500, "MAC Address Table")
    
    # Generate ARP table
    print("\nGenerating ARP table...")
    arp_table_content, arp_table_stats = generate_arp_table(500)
    arp_table_path = write_test_file(arp_table_content, 'test-arp-table.txt', test_data_dir)
    print(f"Generated ARP table -> {arp_table_path}")
    print_vendor_statistics(arp_table_stats, 500, "ARP Table")
    
    # Generate MAC list
    print("\nGenerating MAC address list...")
    mac_list_content, mac_list_stats = generate_mac_list(100)
    mac_list_path = write_test_file(mac_list_content, 'test-mac-list.txt', test_data_dir)
    print(f"Generated MAC list -> {mac_list_path}")
    print_vendor_statistics(mac_list_stats, 100, "MAC List")
    
    # Create README file
    readme_content = """# Test Data Directory

This directory contains generated test data for NetVendor testing.

Files:
1. test-mac-table.txt - Cisco MAC address table (500 entries)
2. test-arp-table.txt - Cisco show ip arp output (500 entries)
3. test-mac-list.txt - Simple MAC address list (100 entries)

These files are automatically generated using generate_test_files.py.
Do not modify these files manually.

The data uses real vendor OUIs and follows realistic vendor distributions:
- Cisco: ~20%
- HP: ~16%
- Dell: ~14%
- Apple: ~12%
- Juniper: ~10%
- Aruba: ~10%
- Extreme: ~8%
- Mitel: ~8%
"""
    write_test_file(readme_content, 'README.md', test_data_dir)

if __name__ == "__main__":
    main()
