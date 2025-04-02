"""
Core functionality for NetVendor package.
"""

import os
import sys
import json
from rich.console import Console
from .oui_manager import OUIManager
from ..utils import (
    make_csv,
    generate_port_report,
    create_vendor_distribution,
    save_vendor_summary
)

console = Console()

def check_dependencies() -> None:
    """
    Validates required modules before script execution to prevent runtime failures.
    """
    modules_to_check = ["requests", "plotly", "tqdm", "rich"]
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            console.print(f"The module '{module_name}' is installed.")
        except ImportError:
            console.print(f"The module '{module_name}' is not installed, this is required to run NetVendor.")
            console.print("\n[bold red]NetVendor will now exit[/bold red]")
            sys.exit(1)

def is_mac_address(mac: str) -> bool:
    """
    Check if a string is a valid MAC address.
    """
    mac = mac.lower().replace(':', '').replace('.', '').replace('-', '')
    if len(mac) != 12:
        return False
    try:
        int(mac, 16)
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

def load_oui_cache() -> dict:
    """
    Load the OUI cache from the package data directory.
    """
    try:
        cache_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'oui_cache.json')
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[bold red]Warning:[/bold red] Could not load OUI cache: {str(e)}")
        return {}

def lookup_vendor(mac: str, oui_cache: dict) -> str:
    """
    Look up a vendor from a MAC address using the OUI cache.
    """
    if not mac:
        return "Unknown"
        
    # Normalize MAC address
    mac = mac.lower().replace(':', '').replace('.', '').replace('-', '')
    if len(mac) < 6:
        return "Unknown"
        
    # Get OUI (first 6 characters)
    oui = mac[:6]
    
    # Format OUI with colons for lookup
    oui_formatted = ':'.join([oui[i:i+2] for i in range(0, 6, 2)])
    
    # Look up vendor
    return oui_cache.get(oui_formatted, "Unknown")

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
        # Read first line to determine file type
        first_line = f.readline().strip()
        
        # Check if it's a MAC list file (first line is a MAC address)
        is_mac_list = is_mac_address(first_line)
        is_arp_table = not is_mac_list and "Internet" in first_line
        is_mac_table = not is_mac_list and not is_arp_table
        
        # Reset file pointer to start
        f.seek(0)
        
        for line in f:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            line_count += 1
            
            if is_mac_list:
                # For MAC list files, treat each line as a potential MAC address
                mac = line.lower()
                if is_mac_address(mac):
                    devices[mac] = {'vlan': 'N/A', 'port': 'N/A'}
                    mac_count += 1
            else:
                words = line.split()
                mac_word = 4 if is_arp_table else 2  # MAC is 4th word in ARP, 2nd in MAC table
                
                if len(words) >= mac_word:
                    mac = words[mac_word - 1].lower()
                    if is_mac_address(mac):
                        if is_arp_table:
                            vlan = words[-1].replace('Vlan', '') if 'Vlan' in words[-1] else 'N/A'
                            port = None  # ARP tables don't have port information
                        else:
                            vlan = words[0] if is_mac_address_table(line) else 'N/A'
                            port = parse_port_info(line)
                            if port:
                                port_count += 1
                        devices[mac] = {'vlan': vlan, 'port': port if port else 'N/A'}
                        mac_count += 1
    
    # Print processing summary
    console.print(f"\nProcessed {line_count} lines")
    if is_mac_list:
        console.print(f"Found {mac_count} MAC addresses")
    elif is_mac_table:
        console.print(f"Found {port_count} port entries")
        console.print(f"Found {len(set(d['port'] for d in devices.values() if d['port'] != 'N/A'))} unique ports")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Generate reports
    make_csv(input_file, devices, oui_manager)
    
    # Only generate port report for MAC address tables
    if is_mac_table:
        generate_port_report(input_file, devices, oui_manager, is_mac_table)
    
    # Create vendor distribution visualization
    create_vendor_distribution(devices, oui_manager, input_file)
    
    # Save vendor summary
    save_vendor_summary(devices, oui_manager, input_file)

if __name__ == "__main__":
    main() 