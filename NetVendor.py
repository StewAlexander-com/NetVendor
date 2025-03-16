#!/usr/bin/env python3

#####################################
#                                   #
#      Created by Stew Alexander    #
#                2021               #
#                                   #
#####################################

import os
import sys
import csv
import time
import subprocess
import shutil
from pathlib import Path
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass
import json
from collections import Counter
import requests
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    DownloadColumn,
    TaskID
)
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import plotly.graph_objects as go

def check_dependencies() -> None:
    """
    Check if all required Python modules are installed.
    Exits the program if any required module is missing.
    """
    modules_to_check = ["requests", "plotly", "tqdm", "rich"]
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"The module '{module_name}' is installed.")
        except ImportError:
            print(f"The module '{module_name}' is not installed, this is required to run NetVendor.")
            print("\n[bold red]NetVendor will now exit[/bold red]")
            sys.exit(1)

def get_input_file() -> Tuple[str, int, int]:
    """Get the input file and determine its type."""
    if len(sys.argv) != 2:
        print("Usage: python3 NetVendor.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
    
    # Determine file type based on content
    if "Internet" in first_line:
        mac_word = 3
        vendor_word = 4
    else:
        mac_word = 1
        vendor_word = 2
    
    return input_file, mac_word, vendor_word

@dataclass
class OUIManager:
    """Manages OUI lookups and caching."""
    cache_file: str = "oui_cache.json"
    cache: Dict[str, str] = None
    
    def __post_init__(self):
        self.load_cache()
    
    def load_cache(self):
        """Load OUI cache from file."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {}
    
    def save_cache(self):
        """Save OUI cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def lookup_vendor(self, mac: str) -> str:
        """Look up vendor for MAC address."""
        oui = mac[:8].upper()
        
        if oui in self.cache:
            return self.cache[oui]
        
        try:
            response = requests.get(f"https://api.macvendors.com/{oui}")
            if response.status_code == 200:
                vendor = response.text
                self.cache[oui] = vendor
                self.save_cache()
                time.sleep(1)  # Rate limiting
                return vendor
            else:
                return "Unknown"
        except:
            return "Unknown"

def process_vendor_devices(ip_arp_file: str, mac_word: int, vendor_word: int, oui_manager: OUIManager) -> Dict[str, int]:
    """Process the input file and return vendor counts."""
    vendor_counts = Counter()
    total_lines = sum(1 for _ in open(ip_arp_file))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Processing MAC addresses...", total=total_lines)
        
        with open(ip_arp_file, 'r') as f:
            for line in f:
                progress.update(task, advance=1)
                if not line.strip() or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) > mac_word:
                    mac = parts[mac_word].replace('.', ':')
                    vendor = oui_manager.lookup_vendor(mac)
                    vendor_counts[vendor] += 1
    
    return vendor_counts

def create_pie_chart(vendor_counts: Dict[str, int]) -> None:
    """Create a pie chart of vendor distribution."""
    labels = list(vendor_counts.keys())
    values = list(vendor_counts.values())
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_layout(
        title="Network Device Vendor Distribution",
        showlegend=True
    )
    
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    fig.write_html(os.path.join(output_dir, "vendor_distribution.html"))

def make_csv(file: str) -> None:
    """Create a CSV file with device information."""
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_file = os.path.join(output_dir, f"{base_name}-Devices.csv")
    
    with open(file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['IP Address', 'MAC Address', 'VLAN', 'Vendor'])
        
        for line in infile:
            if not line.strip() or line.startswith('#'):
                continue
            
            parts = line.split()
            if "Internet" in line and len(parts) >= 6:
                ip = parts[1]
                mac = parts[3].replace('.', ':')
                vlan = parts[5].replace('Vlan', '')
                vendor = OUIManager().lookup_vendor(mac)
                writer.writerow([ip, mac, vlan, vendor])

def main():
    """Main function."""
    check_dependencies()
    
    console = Console()
    console.print("\n[bold cyan]NetVendor - Network Device Vendor Analysis[/bold cyan]")
    console.print("[cyan]Created by Stew Alexander[/cyan]\n")
    
    input_file, mac_word, vendor_word = get_input_file()
    oui_manager = OUIManager()
    
    vendor_counts = process_vendor_devices(input_file, mac_word, vendor_word, oui_manager)
    
    # Create and display results table
    table = Table(title="Network Device Vendor Summary")
    table.add_column("Vendor", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Percentage", style="green")
    
    total_devices = sum(vendor_counts.values())
    for vendor, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_devices) * 100
        table.add_row(vendor, str(count), f"{percentage:.1f}%")
    
    console.print(table)
    
    # Create pie chart
    create_pie_chart(vendor_counts)
    
    # Create CSV file
    make_csv(input_file)
    
    console.print("\n[green]Analysis complete![/green]")
    console.print(f"[cyan]Total devices analyzed: {total_devices}[/cyan]")
    console.print("\n[yellow]Output files have been created in the 'output' directory:[/yellow]")
    console.print("  • vendor_distribution.html (Interactive pie chart)")
    console.print(f"  • {os.path.splitext(os.path.basename(input_file))[0]}-Devices.csv (Detailed device list)")

if __name__ == "__main__":
    main()
