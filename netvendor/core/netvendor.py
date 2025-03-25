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
    
    # Process the input file
    try:
        # Determine if the input is a MAC address table
        with open(input_file, 'r') as f:
            first_lines = [next(f) for _ in range(5)]
            is_mac_table = any(is_mac_address_table(line) for line in first_lines)
        
        from netvendor.utils.vendor_output_handler import (
            make_csv,
            generate_port_report,
            create_vendor_distribution,
            save_vendor_summary
        )
        
        # Process the file and generate outputs
        devices = make_csv(input_file)
        generate_port_report(devices, is_mac_table)
        create_vendor_distribution(devices)
        save_vendor_summary(devices)
        
        console.print("[bold green]Processing complete![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error processing file:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 