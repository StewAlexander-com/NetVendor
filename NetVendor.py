#!/usr/bin/env python3

import os
import sys
import json
import csv
from rich.console import Console

from netvendor.oui_manager import OUIManager
from netvendor.vendor_output_handler import (
    make_csv,
    generate_port_report,
    create_vendor_distribution,
    save_vendor_summary
)

console = Console()

def check_dependencies():
    """
    Check if required modules are installed.
    """
    required_modules = ['requests', 'plotly', 'tqdm', 'rich']
    for module in required_modules:
        try:
            __import__(module)
            console.print(f"The module '{module}' is installed.")
        except ImportError:
            console.print(f"[bold red]Error:[/bold red] Required module '{module}' is not installed.")
            console.print(f"Please install it using: pip install {module}")
            sys.exit(1)

def is_mac_address(mac: str) -> bool:
    """
    Check if a string is a valid MAC address.
    Supports formats:
    - 00:11:22:33:44:55
    - 00-11-22-33-44-55
    - 0011.2233.4455
    - 001122334455
    - D8.C7.C8.14C17B (ARP table format)
    """
    if not mac:
        return False
        
    # Remove all separators and spaces
    mac_clean = mac.strip().lower().replace(':', '').replace('.', '').replace('-', '')
    
    # Check if we have enough characters for a MAC address
    if len(mac_clean) < 12:
        return False
    
    # Take first 12 characters (some formats might have more)
    mac_clean = mac_clean[:12]
    
    # Check if all characters are valid hex
    try:
        int(mac_clean, 16)
        return True
    except ValueError:
        return False

def is_mac_address_table(line: str) -> bool:
    """
    Check if a line is from a MAC address table.
    """
    # Check for header line variations
    if any(all(word in line for word in header) for header in [
        ["Vlan", "Mac Address"],
        ["VLAN", "MAC Address"],
        ["VLAN ID", "MAC Address"]
    ]):
        return True
        
    words = line.strip().split()
    if len(words) < 2:
        return False
    try:
        vlan = int(words[0])
        if not (1 <= vlan <= 4094):
            return False
    except ValueError:
        return False
    return is_mac_address(words[1])

def parse_port_info(line: str) -> str:
    """
    Extract port information from a line.
    """
    if "Internet" in line and "ARPA" in line:
        return None
    words = line.strip().split()
    if len(words) < 2:
        return None
    port = words[-1]
    # Check for common port prefixes
    if any(port.startswith(prefix) for prefix in ['Gi', 'Fa', 'Te', 'Eth']):
        return port
    # Check if it's a simple port number
    try:
        int(port)
        return port
    except ValueError:
    return None

def format_mac_address(mac: str) -> str:
    """
    Format a MAC address consistently.
    Input can be any format, output will be xx:xx:xx:xx:xx:xx
    """
    if not mac:
        return None
        
    # Remove all separators and spaces
    mac_clean = mac.strip().lower().replace(':', '').replace('.', '').replace('-', '')
    
    # Take first 12 characters
    if len(mac_clean) >= 12:
        mac_clean = mac_clean[:12]
        # Format with colons
        return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
    return None

def main():
    """
    Main entry point for the NetVendor package.
    """
    # Check if required modules are installed
    check_dependencies()
    
    # Check if input file is provided
    if len(sys.argv) != 2:
        console.print("[bold red]Error:[/bold red] Please provide an input file.")
        console.print("Usage: netvendor <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Check if input file exists
    if not os.path.exists(input_file):
        console.print(f"[bold red]Error:[/bold red] Input file '{input_file}' not found.")
        sys.exit(1)
    
    # Initialize OUI manager
    oui_manager = OUIManager()
    console.print(f"Loaded OUI cache with {len(oui_manager.cache)} entries")
    
    # Process the input file
    devices = {}
    line_count = 0
    port_count = 0
    mac_count = 0
    
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip() if first_line else ""
        
        # Debug output for file type detection
        console.print(f"\nFile Analysis:")
        console.print(f"First line: {first_line}")
        console.print(f"Second line: {second_line}")
        
        # Check file type
        is_mac_list = is_mac_address(first_line)
        is_arp_table = not is_mac_list and (
            first_line.startswith("Protocol") or  # ARP table header
            "Internet" in first_line or           # First data line
            "Internet" in second_line             # Second line for ARP tables
        )
        is_mac_table = not is_mac_list and not is_arp_table
        
        console.print(f"\nFile Type Detection:")
        console.print(f"  is_mac_list: {is_mac_list}")
        console.print(f"  is_arp_table: {is_arp_table}")
        console.print(f"  is_mac_table: {is_mac_table}")
        
        # Reset to start of file
        f.seek(0)
        
        for line in f:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            
            line_count += 1
            
            if is_mac_list:
                mac = line.lower()
                if is_mac_address(mac):
                    mac_formatted = format_mac_address(mac)
                    if mac_formatted:
                        devices[mac_formatted] = {'vlan': 'N/A', 'port': 'N/A'}
                        mac_count += 1
                        console.print(f"Added MAC list entry: {mac_formatted}")
            elif is_arp_table:
                # Skip the header line
                if "Protocol" in line:
                        continue
                    
                # Use string split with maxsplit to preserve spacing
                parts = line.split(None, 5)  # Split into 6 parts max
                console.print(f"\nProcessing line: {line}")
                console.print(f"Split parts: {parts}")
                
                if len(parts) >= 6 and parts[0] == "Internet":
                    mac = parts[3].strip()  # Hardware address is the 4th field
                    interface = parts[5].strip()  # Interface is the last field
                    
                    console.print(f"Found MAC: {mac}")
                    console.print(f"Interface: {interface}")
                    
                    mac_formatted = format_mac_address(mac)
                    if mac_formatted:
                        vlan = interface.replace('Vlan', '') if 'Vlan' in interface else 'N/A'
                        devices[mac_formatted] = {'vlan': vlan, 'port': 'N/A'}
                        mac_count += 1
                        console.print(f"Added MAC: {mac_formatted} with VLAN: {vlan}")
            else:
                # MAC table processing
                words = line.split()
                if len(words) >= 2:
                    mac = words[1]
                    mac_formatted = format_mac_address(mac)
                    if mac_formatted:
                        vlan = words[0] if is_mac_address_table(line) else 'N/A'
                        port = parse_port_info(line)
                        if port:
                            port_count += 1
                        devices[mac_formatted] = {'vlan': vlan, 'port': port if port else 'N/A'}
                        mac_count += 1
                        console.print(f"Added MAC table entry: {mac_formatted} (VLAN: {vlan}, Port: {port if port else 'N/A'})")
    
    # Print processing summary
    console.print(f"\nProcessing Summary:")
    console.print(f"Processed {line_count} lines")
    console.print(f"Found {mac_count} MAC addresses")
    console.print(f"Total devices in dictionary: {len(devices)}")
    
    if len(devices) == 0:
        console.print("[bold red]Warning:[/bold red] No MAC addresses were processed!")
        sys.exit(1)
    
    # Show sample of processed devices
    console.print("\nSample of processed devices:")
    for i, (mac, info) in enumerate(devices.items()):
        if i >= 5:  # Show first 5 entries
                    break
        console.print(f"  {mac}: {info}")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Generate reports
    output_file = os.path.join('output', os.path.basename(input_file).replace('.txt', '-Devices.csv'))
    console.print(f"\nWriting to CSV file: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vlan = info.get('vlan', 'N/A')
            port = info.get('port', 'N/A')
            writer.writerow([mac, vendor, vlan, port])
            console.print(f"Wrote: {mac}, {vendor}, {vlan}, {port}")
    
    # Verify the file was written
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            content = f.read()
            console.print(f"\nOutput file content (first few lines):")
            console.print(content[:500])  # Show first 500 characters
                    else:
        console.print("[bold red]Error:[/bold red] Output file was not created!")
    
    # Generate additional reports
    if is_mac_table:
        generate_port_report(input_file, devices, oui_manager, is_mac_table)
    
    create_vendor_distribution(devices, oui_manager, input_file)
    save_vendor_summary(devices, oui_manager, input_file)

if __name__ == "__main__":
    main()