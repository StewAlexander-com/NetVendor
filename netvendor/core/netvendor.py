"""
Core functionality for NetVendor package.
"""

import os
import sys
from rich.console import Console

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