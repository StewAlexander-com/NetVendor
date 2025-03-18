#!/usr/bin/env python3

"""
Generate test data for NetVendor with 500 MAC address entries
"""

import random

# Vendor OUI definitions
VENDORS = {
    'Cisco': ['00:00:0C', '00:0E:83', '00:1A:A0', '00:23:EB'],
    'HP': ['00:1C:C4', '00:24:81', '00:25:B3', '00:60:B0'],
    'Dell': ['00:14:22', '00:1E:4F', 'B8:AC:6F', '00:1E:C9'],
    'Apple': ['00:03:93', '00:0A:27', '00:1B:63'],
    'Mitel': ['00:90:7F', '08:00:0F']
}

def generate_mac_suffix():
    """Generate random MAC address suffix"""
    return f"{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"

def generate_ip(start=1):
    """Generate IP address in 192.168.x.y format"""
    subnet = (start - 1) // 254 + 1
    host = ((start - 1) % 254) + 1
    return f"192.168.{subnet}.{host}"

def generate_entry(index, vendor, oui):
    """Generate a single ARP entry"""
    mac_suffix = generate_mac_suffix()
    ip = generate_ip(index)
    vlan = ((index - 1) // 50) * 100 + 100  # Changes VLAN every 50 entries
    return f"Internet  {ip:<15} 1   {oui}:{mac_suffix}  ARPA   Vlan{vlan}"

def main():
    # Generate entries
    entries = []
    index = 1
    
    # Distribute vendors
    vendor_counts = {
        'Cisco': 150,  # 30%
        'HP': 125,     # 25%
        'Dell': 100,   # 20%
        'Apple': 75,   # 15%
        'Mitel': 50    # 10%
    }
    
    for vendor, count in vendor_counts.items():
        ouis = VENDORS[vendor]
        for _ in range(count):
            oui = random.choice(ouis)
            entry = generate_entry(index, vendor, oui)
            entries.append(entry)
            index += 1
    
    # Shuffle entries to mix vendors
    random.shuffle(entries)
    
    # Write entries to file
    with open('ip-arp-test.txt', 'w') as f:
        for entry in entries:
            f.write(f"{entry}\n")

if __name__ == "__main__":
    main() 