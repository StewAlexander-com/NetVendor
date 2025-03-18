#!/usr/bin/env python3

"""
Generate test data for NetVendor with 2500 MAC address entries
"""

import random

# Extended Vendor OUI definitions
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
    vlan = random.randint(1, 50) * 10  # Random VLAN between 10 and 500
    return f"Internet  {ip:<15} 1   {oui}:{mac_suffix}  ARPA   Vlan{vlan}"

def main():
    # Generate entries
    entries = []
    index = 1
    
    # Distribute vendors with more randomization
    # Base distribution but with variation
    vendor_counts = {
        'Cisco': random.randint(400, 600),     # ~20%
        'HP': random.randint(300, 500),        # ~16%
        'Dell': random.randint(250, 450),      # ~14%
        'Apple': random.randint(200, 400),     # ~12%
        'Juniper': random.randint(150, 350),   # ~10%
        'Aruba': random.randint(150, 350),     # ~10%
        'Extreme': random.randint(100, 300),   # ~8%
        'Mitel': random.randint(100, 300)      # ~8%
    }
    
    # Ensure we get exactly 2500 entries
    total = sum(vendor_counts.values())
    scale_factor = 2500 / total
    
    for vendor in vendor_counts:
        vendor_counts[vendor] = int(vendor_counts[vendor] * scale_factor)
    
    # Adjust any rounding errors to hit exactly 2500
    total = sum(vendor_counts.values())
    if total < 2500:
        vendor_counts['Cisco'] += 2500 - total
    elif total > 2500:
        vendor_counts['Cisco'] -= total - 2500
    
    # Generate entries for each vendor
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

    # Print summary
    print("\nGenerated 2500 entries with the following distribution:")
    for vendor, count in vendor_counts.items():
        percentage = (count / 2500) * 100
        print(f"{vendor:8}: {count:4} entries ({percentage:5.1f}%)")

if __name__ == "__main__":
    main() 