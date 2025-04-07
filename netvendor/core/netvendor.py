import os
import sys
from rich.console import Console
from ..utils.vendor_output_handler import make_csv, generate_port_report, create_vendor_distribution, save_vendor_summary
from .oui_manager import OUIManager

console = Console()

def check_dependencies():
    """Check if required modules are installed."""
    required_modules = ['requests', 'plotly', 'tqdm', 'rich']
    for module in required_modules:
        try:
            __import__(module)
            console.print(f"The module '{module}' is installed.")
        except ImportError:
            console.print(f"[red]Error: The module '{module}' is not installed.[/red]")
            console.print(f"Please install it using: pip install {module}")
            sys.exit(1)

def is_mac_address(mac: str) -> bool:
    """
    Check if a string is a valid MAC address in standard format.
    For MAC address list files only.
    Supports formats:
    - 00:11:22:33:44:55
    - 00-11-22-33-44-55
    - 001122334455
    """
    if not mac:
        return False
        
    # Remove all separators and spaces
    mac_clean = mac.strip().lower().replace(':', '').replace('-', '')
    
    # Check length
    if len(mac_clean) != 12:
        return False
        
    # Check if all characters are valid hex
    try:
        int(mac_clean, 16)
        return True
    except ValueError:
        return False

def is_arp_table_mac(mac: str) -> bool:
    """
    Check if a string is a valid MAC address in ARP table format.
    Handles dot notation format like: D8.C7.C8.14C17B
    """
    if not mac:
        return False
    
    # Split by dots and check we have parts
    parts = mac.strip().split('.')
    if len(parts) != 4:
        return False
    
    # Join parts and check if it's valid hex
    mac_clean = ''.join(parts)[:12]  # Take first 12 chars in case of longer format
    try:
        int(mac_clean, 16)
        return True
    except ValueError:
        return False

def format_mac_address(mac: str) -> str:
    """
    Format a MAC address consistently.
    Input can be any format, output will be xx:xx:xx:xx:xx:xx
    """
    if not mac:
        return None
    
    # Handle dot notation (ARP table format)
    if '.' in mac:
        parts = mac.strip().split('.')
        mac_clean = ''.join(parts)[:12]
    else:
        # Handle standard formats
        mac_clean = mac.strip().lower().replace(':', '').replace('-', '')
    
    # Take first 12 characters and format with colons
    if len(mac_clean) >= 12:
        mac_clean = mac_clean[:12]
        return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
    return None

def is_arp_table(line: str) -> bool:
    """
    Check if a line is from an ARP table.
    Returns True if the line matches ARP table format.
    """
    # Check for header
    if "Protocol" in line and "Address" in line and "Hardware Addr" in line:
        return True
    
    # Check for data line format
    parts = line.split(None, 5)  # Split into max 6 parts
    if len(parts) >= 6:
        # Check if first field is "Internet"
        if parts[0] != "Internet":
            return False
        
        # Check if fourth field (hardware address) is in MAC format
        mac = parts[3].strip()
        return is_arp_table_mac(mac)
    
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
    """Extract port information from a line."""
    words = line.strip().split()
    if len(words) >= 4:
        return words[-1]
    return None

def process_arp_line(line: str) -> tuple[str, str]:
    """
    Process a line from an ARP table and extract MAC address and VLAN.
    Returns tuple of (formatted_mac, vlan) or (None, None) if invalid.
    """
    parts = line.split(None, 5)
    if len(parts) >= 6 and parts[0] == "Internet":
        mac = parts[3].strip()
        interface = parts[5].strip()
        
        if is_arp_table_mac(mac):
            mac_formatted = format_mac_address(mac)
            vlan = interface.replace('Vlan', '') if 'Vlan' in interface else 'N/A'
            return mac_formatted, vlan
    
    return None, None

def main():
    """Main function to process input file and generate reports."""
    # Check command line arguments
    if len(sys.argv) != 2:
        console.print("[red]Error: Please provide an input file.[/red]")
        console.print("Usage: netvendor <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Check if input file exists
    if not os.path.exists(input_file):
        console.print(f"[red]Error: Input file '{input_file}' not found.[/red]")
        sys.exit(1)

    # Check dependencies
    check_dependencies()

    # Initialize OUI manager
    oui_manager = OUIManager()

    # Dictionary to store device information
    devices = {}
    line_count = 0
    port_count = 0
    mac_count = 0
    
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip() if first_line else ""
        
        # Check file type
        is_mac_list = is_mac_address(first_line)
        is_arp = is_arp_table(first_line) or (second_line and is_arp_table(second_line))
        is_mac_table = not is_mac_list and not is_arp
        
        # Reset to start of file
        f.seek(0)
        
        # Skip header for ARP table
        if is_arp:
            next(f)  # Skip the header line
        
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
            elif is_arp:
                # Skip the header line
                if "Protocol" in line:
                    continue
                
                mac_formatted, vlan = process_arp_line(line)
                if mac_formatted:
                    devices[mac_formatted] = {'vlan': vlan, 'port': 'N/A'}
                    mac_count += 1
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
    
    # Print processing summary
    console.print(f"\nProcessed {line_count} lines")
    console.print(f"Found {mac_count} MAC addresses")
    if is_mac_table:
        console.print(f"Found {port_count} port entries")
        console.print(f"Found {len(set(d['port'] for d in devices.values() if d['port'] != 'N/A'))} unique ports")
    
    if len(devices) == 0:
        console.print("[bold red]Warning:[/bold red] No MAC addresses were processed!")
        sys.exit(1)
    
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