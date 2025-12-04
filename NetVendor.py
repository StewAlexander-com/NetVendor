#!/usr/bin/env python3

import os
import sys
import json
import csv
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timezone
from rich.console import Console

from netvendor.core.oui_manager import OUIManager
from netvendor.utils.vendor_output_handler import (
    make_csv,
    generate_port_report,
    create_vendor_distribution,
    save_vendor_summary
)
from netvendor.utils.drift_analysis import analyze_drift
from netvendor.utils.siem_export import export_siem_events

console = Console()
VERBOSE = os.getenv("NETVENDOR_VERBOSE", "0") in ("1", "true", "True")

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

    parser = argparse.ArgumentParser(
        description="Analyze network MAC/ARP data and generate vendor distribution reports."
    )
    parser.add_argument(
        "input_file",
        help="Path to MAC address list, MAC table, or ARP table file."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Disable external vendor lookups and use only the local OUI cache. "
             "Uncached devices will appear as 'Unknown'."
    )
    parser.add_argument(
        "--history-dir",
        default="history",
        help="Directory to archive vendor_summary snapshots for drift analysis "
             "(default: ./history)."
    )
    parser.add_argument(
        "--analyze-drift",
        action="store_true",
        help="After archiving the latest vendor_summary snapshot, run drift analysis "
             "over all archived summaries and write vendor_drift.csv."
    )
    parser.add_argument(
        "--site",
        default=None,
        help="Optional site/region identifier tag to include in SIEM exports (e.g., DC1, HQ, us-east-1)."
    )
    parser.add_argument(
        "--environment",
        default=None,
        help="Optional environment identifier tag to include in SIEM exports (e.g., prod, dev, staging)."
    )
    parser.add_argument(
        "--change-ticket",
        default=None,
        help="Optional change ticket/incident ID for drift analysis correlation (e.g., CHG-12345, INC-67890). "
             "Stored in drift metadata for 8D/5-why incident analysis workflows."
    )
    parser.add_argument(
        "--siem-export",
        action="store_true",
        help="Export normalized CSV/JSONL events for SIEM ingestion "
             "(netvendor_siem.csv / netvendor_siem.json in output/siem/ directory). "
             "Each record includes: timestamp, site, environment, mac, vendor, device_name, vlan, interface, input_type, source_file."
    )

    args = parser.parse_args()
    input_file = args.input_file

    # Check if input file exists
    if not os.path.exists(input_file):
        console.print(f"[bold red]Error:[/bold red] Input file '{input_file}' not found.")
        sys.exit(1)

    # Initialize OUI manager
    oui_manager = OUIManager(offline=args.offline)
    if args.offline:
        console.print(
            "[yellow]Offline mode enabled:[/yellow] external vendor lookups are disabled. "
            "Devices not present in the local cache will appear as 'Unknown'."
        )
    if VERBOSE:
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
        if VERBOSE:
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
        
        if VERBOSE:
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
                        if VERBOSE:
                            console.print(f"Added MAC list entry: {mac_formatted}")
            elif is_arp_table:
                # Skip the header line
                if "Protocol" in line:
                    continue
                    
                # Use string split with maxsplit to preserve spacing
                parts = line.split(None, 5)  # Split into 6 parts max
                if VERBOSE:
                    console.print(f"\nProcessing line: {line}")
                    console.print(f"Split parts: {parts}")
                
                if len(parts) >= 6 and parts[0] == "Internet":
                    mac = parts[3].strip()  # Hardware address is the 4th field
                    interface = parts[5].strip()  # Interface is the last field
                    
                    if VERBOSE:
                        console.print(f"Found MAC: {mac}")
                        console.print(f"Interface: {interface}")
                    
                    mac_formatted = format_mac_address(mac)
                    if mac_formatted:
                        vlan = interface.replace('Vlan', '') if 'Vlan' in interface else 'N/A'
                        devices[mac_formatted] = {'vlan': vlan, 'port': 'N/A'}
                        mac_count += 1
                        if VERBOSE:
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
                        if VERBOSE:
                            console.print(f"Added MAC table entry: {mac_formatted} (VLAN: {vlan}, Port: {port if port else 'N/A'})")
    
    # Print processing summary
    console.print(f"\nProcessing Summary:")
    console.print(f"Processed {line_count} lines")
    console.print(f"Found {mac_count} MAC addresses")
    if VERBOSE:
        console.print(f"Total devices in dictionary: {len(devices)}")
    
    if len(devices) == 0:
        console.print("[bold red]Warning:[/bold red] No MAC addresses were processed!")
        sys.exit(1)
    
    # Show sample of processed devices
    if VERBOSE:
        console.print("\nSample of processed devices:")
        for i, (mac, info) in enumerate(devices.items()):
            if i >= 5:  # Show first 5 entries
                break
            console.print(f"  {mac}: {info}")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Generate reports
    output_file = os.path.join('output', os.path.basename(input_file).replace('.txt', '-Devices.csv'))
    if VERBOSE:
        console.print(f"\nWriting to CSV file: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vlan = info.get('vlan', 'N/A')
            port = info.get('port', 'N/A')
            writer.writerow([mac, vendor, vlan, port])
            if VERBOSE:
                console.print(f"Wrote: {mac}, {vendor}, {vlan}, {port}")
    
    # Verify the file was written
    if os.path.exists(output_file):
        if VERBOSE:
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

    # Optional SIEM export
    if args.siem_export:
        if is_mac_list:
            input_type = "mac_list"
        elif is_arp_table:
            input_type = "arp_table"
        elif is_mac_table:
            input_type = "mac_table"
        else:
            input_type = "unknown"
        export_siem_events(
            devices=devices,
            oui_manager=oui_manager,
            input_file=input_file,
            site=args.site,
            environment=args.environment,
            input_type=input_type,
        )

    # Archive vendor summary for drift analysis with metadata
    history_dir = Path(args.history_dir)
    history_dir.mkdir(parents=True, exist_ok=True)
    summary_src = Path("output") / "vendor_summary.txt"
    if summary_src.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        summary_dst = history_dir / f"vendor_summary-{timestamp}.txt"
        try:
            shutil.copy2(summary_src, summary_dst)
            
            # Write companion metadata file for drift analysis correlation
            metadata = {
                "run_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "site": args.site,
                "change_ticket_id": args.change_ticket,
            }
            metadata_path = history_dir / f"{summary_dst.stem}.metadata.json"
            with metadata_path.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            if VERBOSE:
                console.print(f"Archived vendor summary to [green]{summary_dst}[/green]")
                console.print(f"Archived metadata to [green]{metadata_path}[/green]")
        except OSError as e:
            console.print(f"[yellow]Warning:[/yellow] Could not archive vendor summary: {e}")

    # Optionally run drift analysis over archived summaries
    if args.analyze_drift:
        try:
            drift_csv = analyze_drift(history_dir)
            console.print(f"Vendor drift analysis written to [green]{drift_csv}[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Drift analysis failed: {e}")

if __name__ == "__main__":
    main()