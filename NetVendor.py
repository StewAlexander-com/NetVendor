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
import plotly.graph_objs as go
import pandas as pd
from oui_manager import OUIManager
import matplotlib.pyplot as plt

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
        sys.exit()

def get_input_file() -> Tuple[str, int, int]:
    """
    Get the input file and column information from user.
    Returns:
        Tuple containing:
        - input file name
        - MAC address column index (0-based)
        - VLAN column index (0-based)
    """
    cwd = os.getcwd()
    print("\nPlease select the [italic green]ARP[/italic green] or [italic green]MAC[/italic green] Data text file from [cyan]"+cwd+"[/cyan] \n")
    print(os.listdir(), "\n")

    while True:
        ip_arp_file = input("Please enter the file name: ")
        if os.path.isfile(ip_arp_file):
            break
        print("\n[italic yellow]The file name is not valid, please try again[/italic yellow]\n")

    print("Please enter the column in the file that contains the [cyan]Mac Addresses[/cyan]:")
    mac_column = int(input("> "))
    mac_word = mac_column - 1

    print("\nPlease enter the column in the file that contains the [cyan]VLANs[/cyan]:")
    vlan_column = int(input("> "))
    vlan_word = vlan_column - 1

    return ip_arp_file, mac_word, vlan_word

def process_vendor_devices(ip_arp_file: str, mac_word: int, vendor: str, oui_manager: OUIManager) -> int:
    """
    Process devices for a specific vendor and create corresponding output files.
    
    Args:
        ip_arp_file: Path to the input file
        mac_word: Index of the MAC address column
        vendor: Vendor name (e.g., "Apple", "Dell", etc.)
        oui_manager: Instance of OUIManager for OUI lookups
    
    Returns:
        Number of devices found for this vendor
    """
    output_file = f"{vendor}-Devices.txt"
    
    # Delete existing output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)
    
    print(f"\nFinding any [cyan]{vendor}[/cyan] devices in the [italic green]{ip_arp_file}[/italic green] file....")
    
    # Get vendor OUIs from the manager
    vendor_ouis = oui_manager.get_vendor_ouis(vendor)
    
    # Process the file
    device_count = 0
    
    # First count total lines for progress bar
    with open(ip_arp_file, 'r') as f:
        total_lines = sum(1 for _ in f)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(f"[cyan]Processing {vendor} devices...", total=total_lines)
        
        with open(ip_arp_file, 'r') as input_file, open(output_file, 'a') as output:
            for line in input_file:
                words = line.split()
                if any(words[mac_word].lower().startswith(oui) for oui in vendor_ouis):
                    output.write(line)
                    device_count += 1
                progress.update(task, advance=1)
                
    return device_count

def create_pie_chart(vendor_counts: Dict[str, int]) -> None:
    """
    Create a pie chart from vendor device counts.
    
    Args:
        vendor_counts: Dictionary mapping vendor names to their device counts
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Creating pie chart...", total=4)
        
        # Sort vendors by count
        progress.update(task, description="[cyan]Sorting data...", advance=1)
        sorted_vendors = dict(sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True))
        
        # Prepare plot data
        progress.update(task, description="[cyan]Preparing plot data...", advance=1)
        plt.figure(figsize=(10, 8))
        plt.pie(sorted_vendors.values(), labels=sorted_vendors.keys(), autopct='%1.1f%%')
        plt.title('Network Device Vendors')
        
        # Ensure output/plots directory exists
        progress.update(task, description="[cyan]Creating directory...", advance=1)
        output_dir = Path("output")
        plots_dir = output_dir / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # Save plot
        progress.update(task, description="[cyan]Saving plot...", advance=1)
        plt.savefig(plots_dir / 'vendor_distribution.png')
        plt.close()

def make_csv(file: str) -> None:
    """
    Convert a text file to CSV format and move it to the csv_files directory.
    
    Args:
        file: Path to the text file to convert
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        # Count lines for progress tracking
        progress.add_task("[yellow]Counting lines...", total=None)
        with open(file, 'r') as f:
            total_lines = sum(1 for _ in f)
        
        # Read and process the file
word_list = []
        read_task = progress.add_task("[cyan]Reading file...", total=total_lines)
        with open(file, 'r') as f:
            for line in f:
                words = line.split()
                word_list.append(words)
                progress.update(read_task, advance=1)
        
        # Create CSV file
        csv_file = file.replace(".txt", ".csv")
        
        # Write to CSV
        write_task = progress.add_task("[cyan]Writing CSV...", total=len(word_list))
        with open(csv_file, 'w') as f:
            writer = csv.writer(f)
            for row in word_list:
                writer.writerow(row)
                progress.update(write_task, advance=1)
        
        # Clean up newlines
        cleanup_task = progress.add_task("[cyan]Cleaning up file...", total=None)
        with open(csv_file, 'r') as f:
            data = f.read().replace('\r', '').replace('\n\n', '\n')
        
        with open(csv_file, 'w') as f:
            f.write(data)
        progress.update(cleanup_task, completed=True)
        
        # Ensure output/csv_files directory exists
        output_dir = Path("output")
        csv_dir = output_dir / "csv_files"
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file if it doesn't exist in destination
        move_task = progress.add_task("[cyan]Moving file...", total=None)
        if not (csv_dir / csv_file).exists():
            shutil.move(csv_file, csv_dir / csv_file)
        progress.update(move_task, completed=True)

def main():
    """Main function that orchestrates the NetVendor workflow."""
    # Print banner
print('''[yellow]
888888ba             dP   dP     dP                         dP                   
88    `8b            88   88     88                         88                   
88     88 .d8888b. d8888P 88    .8P .d8888b. 88d888b. .d888b88 .d8888b. 88d888b. 
88     88 88ooood8   88   88    d8' 88ooood8 88'  `88 88'  `88 88'  `88 88'  `88 
88     88 88.  ...   88   88  .d8P  88.  ... 88    88 88.  .88 88.  .88 88       
dP     dP `88888P'   dP   888888'   `88888P' dP    dP `88888P8 `88888P' dP       
[/yellow]''')

print('''[bright_blue]
 ┌─────────────────────────────────────────────────────┐
 │  [white]This app takes the output of a MAC Address Table[/white]   │
 │  [white]or IP ARP and finds all the vendors.[/white]               │
 │                                                     │
 │  [bright_red]Plus:[/bright_red]                                              │
 │  [white]It also collects the Apples, Ciscos, Dells, HPs[/white]    │
 │  [white]and Mitel Phones in your network into csv files[/white]    │
 │  [white]that you can easily import into a spreadsheet[/white]      │
 └─────────────────────────────────────────────────────┘
[/bright_blue]''')

    # Check dependencies
    check_dependencies()

    # Initialize OUI manager and check for updates
    oui_manager = OUIManager()
    if oui_manager.check_update_needed():
        oui_manager.update_database()

    # Get input file and column information
    ip_arp_file, mac_word, vlan_word = get_input_file()

    # Create output directory structure
    output_dir = Path("output")
    text_dir = output_dir / "text_files"
    output_dir.mkdir(exist_ok=True)
    text_dir.mkdir(exist_ok=True)

    # Process each vendor
    vendors = ["Apple", "Dell", "Cisco", "HP", "Mitel"]
    device_counts = {}
    
    for vendor in vendors:
        device_counts[vendor] = process_vendor_devices(ip_arp_file, mac_word, vendor, oui_manager)

    # Calculate total and other devices
    with open(ip_arp_file, 'r') as f:
        total_devices = sum(1 for _ in f) - 1  # Subtract 1 for header
    
    device_counts["Other"] = total_devices - sum(device_counts.values())

    # Display results
    print("\n[bold yellow]Device Counts in the [italic green]" + ip_arp_file + "[/italic green] file:[/bold yellow]\n")
    for vendor, count in device_counts.items():
        print(f"[bright_green]#[/bright_green] [bright_red]{count}[/bright_red] [cyan]{vendor} devices[/cyan]")
print("\n")

    # Create pie chart
    create_pie_chart(device_counts)

    # Convert text files to CSV
    print("[bold yellow]Created file list in the [cyan]text_files[/cyan] folder:[/bold yellow]\n")
    for vendor in vendors:
        vendor_file = f"{vendor}-Devices.txt"
        if os.path.exists(vendor_file):
            print(f"[magenta]>>>[/magenta][italic green] {vendor_file}[/italic green] file for the list of [cyan]{vendor}[/cyan] devices")
            make_csv(vendor_file)

    # Clean up and organize files
for file in os.listdir():
    if file.endswith(".txt"):
            if not (text_dir / file).exists():
                shutil.move(file, text_dir / file)
        else:
                print(f"[bold red]##[/bold red] The [cyan]{file}[/cyan] file already exists in the [cyan]text_files[/cyan] folder")

    # Exit message
input("\nPress enter to quit: ")
time.sleep(3)

if __name__ == "__main__":
    main()
