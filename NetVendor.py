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
from plotly.subplots import make_subplots

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

def create_visualizations(vendor_counts: Dict[str, int], vlan_data: List[str]) -> None:
    """Create interactive visualizations of vendor and VLAN distributions."""
    # Process VLAN data
    vlan_vendor_data = {}  # VLAN -> {vendor: count}
    vendor_vlan_data = {}  # Vendor -> {vlan: count}
    
    for line in vlan_data:
        if "Vlan" not in line or not line.strip():
            continue
        
        parts = line.split()
        if len(parts) >= 6:
            mac = parts[3].replace('.', ':')
            vlan = parts[5].replace('Vlan', '')
            vendor = OUIManager().lookup_vendor(mac)
            
            # Update VLAN -> vendor mapping
            if vlan not in vlan_vendor_data:
                vlan_vendor_data[vlan] = Counter()
            vlan_vendor_data[vlan][vendor] += 1
            
            # Update Vendor -> VLAN mapping
            if vendor not in vendor_vlan_data:
                vendor_vlan_data[vendor] = Counter()
            vendor_vlan_data[vendor][vlan] += 1
    
    # Create two figures for the two pages
    
    # Page 1: Vendor Distribution
    fig1 = go.Figure()
    
    # Vendor Distribution Pie Chart
    labels = list(vendor_counts.keys())
    values = list(vendor_counts.values())
    total_devices = sum(values)
    
    # Create hover text with detailed information
    hover_text = [
        f"Vendor: {label}<br>" +
        f"Count: {value} devices<br>" +
        f"Percentage: {(value/total_devices)*100:.1f}%<br>" +
        f"VLANs: {len(vendor_vlan_data.get(label, []))}"
        for label, value in zip(labels, values)
    ]

    # Create labels with device counts for the legend
    legend_labels = [f"{label} ({value} devices)" for label, value in zip(labels, values)]
    
    fig1.add_trace(
        go.Pie(
            labels=legend_labels,  # Use labels with counts for the legend
            values=values,
            hovertemplate="%{customdata}<br><extra></extra>",
            customdata=hover_text,
            name="Vendor Distribution",
            domain={'x': [0.05, 0.45], 'y': [0.1, 0.9]},  # Moved right boundary of pie chart left
            legendgroup="vendor_dist",
            showlegend=True,
            textinfo='text',  # Show only the text we specify
            textposition='auto',
            text=labels,  # Just show vendor names on the segments
            legendgrouptitle_text="Vendor Distribution",
            textfont=dict(
                size=10,  # Slightly smaller font for the smaller pie
                color='black'
            )
        )
    )
    
    # Update layout for page 1
    fig1.update_layout(
        title="Network Device Vendor Distribution",
        showlegend=True,
        height=900,  # Increased height
        width=1600,
        legend=dict(
            x=0.7,  # Moved legend further right
            y=0.5,
            xanchor='left',
            yanchor='middle',
            font=dict(size=12),
            itemsizing='constant',
            itemwidth=40,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1,
            traceorder='normal'  # Maintain the order of items
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        ),
        margin=dict(l=50, r=50, t=50, b=50)  # Reduced margins to give more space to pie
    )

    # Page 2: VLAN Analysis
    fig2 = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            "VLAN Device Count",
            "VLAN Distribution per Vendor"
        ),
        vertical_spacing=0.15,
        row_heights=[0.3, 0.7]
    )
    
    # VLAN Distribution Bar Chart
    sorted_vlans = sorted(vlan_vendor_data.keys(), key=int)
    vlan_total_counts = [sum(vlan_vendor_data[vlan].values()) for vlan in sorted_vlans]
    vlan_vendor_counts = [len(vlan_vendor_data[vlan]) for vlan in sorted_vlans]
    
    fig2.add_trace(
        go.Bar(
            x=[f"VLAN {v}" for v in sorted_vlans],
            y=vlan_total_counts,
            name="Total Devices",
            hovertemplate="VLAN: %{x}<br>Total Devices: %{y}<br>Unique Vendors: %{customdata}<extra></extra>",
            customdata=vlan_vendor_counts,
            marker_color='rgb(55, 83, 109)'
        ),
        row=1, col=1
    )
    
    # VLAN Distribution per Vendor Heatmap
    vendors_sorted = sorted(vendor_counts.keys(), key=lambda x: vendor_counts[x], reverse=True)
    vlans_sorted = sorted(sorted_vlans, key=int)
    
    heatmap_data = []
    for vendor in vendors_sorted:
        row = []
        for vlan in vlans_sorted:
            count = vendor_vlan_data.get(vendor, {}).get(vlan, 0)
            row.append(count)
        heatmap_data.append(row)
    
    fig2.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=[f"VLAN {v}" for v in vlans_sorted],
            y=vendors_sorted,
            colorscale='Viridis',
            name="VLAN per Vendor",
            hoverongaps=False,
            hovertemplate="Vendor: %{y}<br>%{x}<br>Devices: %{z}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Update layout for page 2
    fig2.update_layout(
        title="VLAN Analysis Dashboard",
        showlegend=True,
        height=1200,
        width=1600,
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        ),
        margin=dict(l=150, r=100, t=100, b=50)
    )
    
    # Update axes labels for page 2
    fig2.update_xaxes(title_text="VLAN", row=1, col=1)
    fig2.update_yaxes(title_text="Number of Devices", row=1, col=1)
    
    # Save visualizations
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Combine both figures into one HTML file with two pages
    with open(os.path.join(output_dir, "vendor_distribution.html"), 'w') as f:
        f.write("""
        <html>
        <head>
            <style>
                body {
                    max-width: 1800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .page-nav {
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: white;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    z-index: 1000;
                }
                .page-nav a {
                    margin: 0 10px;
                    text-decoration: none;
                    color: #333;
                    font-weight: bold;
                }
                .page {
                    display: none;
                    width: 100%;
                }
                .page.active {
                    display: block;
                }
                .js-plotly-plot {
                    margin: 0 auto;
                }
            </style>
            <script>
                function showPage(pageNum) {
                    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
                    document.getElementById('page' + pageNum).classList.add('active');
                }
                window.onload = function() {
                    showPage(1);
                }
            </script>
        </head>
        <body>
            <div class="page-nav">
                <a href="#" onclick="showPage(1); return false;">Vendor Distribution</a>
                <a href="#" onclick="showPage(2); return false;">VLAN Analysis</a>
            </div>
            <div id="page1" class="page">
        """)
        f.write(fig1.to_html(full_html=False))
        f.write('</div><div id="page2" class="page">')
        f.write(fig2.to_html(full_html=False))
        f.write('</div></body></html>')

def process_vendor_devices(ip_arp_file: str, mac_word: int, vendor_word: int, oui_manager: OUIManager) -> Tuple[Dict[str, int], List[str]]:
    """Process the input file and return vendor counts and VLAN data."""
    vendor_counts = Counter()
    vlan_data = []
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
                    vlan_data.append(line)
    
    return vendor_counts, vlan_data

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

def create_text_summary(vendor_counts: Dict[str, int], output_dir: str) -> None:
    """Create a plain text summary of vendor distribution."""
    total_devices = sum(vendor_counts.values())
    
    # Calculate the width needed for the vendor column
    max_vendor_length = max(len(vendor) for vendor in vendor_counts.keys())
    vendor_width = max(max_vendor_length, 6)  # minimum width of 6 for "Vendor"
    
    # Create the header
    header = "Network Device Vendor Summary\n"
    separator = "+{:-<{vendor_width}}+-------+------------+\n".format("", vendor_width=vendor_width)
    column_header = "| {:<{vendor_width}} | Count | Percentage |\n".format("Vendor", vendor_width=vendor_width)
    
    # Create the rows
    rows = []
    for vendor, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_devices) * 100
        row = "| {:<{vendor_width}} | {:<5} | {:<10.1f}% |\n".format(
            vendor, count, percentage, vendor_width=vendor_width
        )
        rows.append(row)
    
    # Write to file
    with open(os.path.join(output_dir, "vendor_summary.txt"), 'w') as f:
        f.write(header)
        f.write(separator)
        f.write(column_header)
        f.write(separator.replace('-', '='))  # Double separator under headers
        for row in rows:
            f.write(row)
        f.write(separator)

def main():
    """Main function."""
    check_dependencies()
    
    console = Console()
    console.print("\n[bold cyan]NetVendor - Network Device Vendor Analysis[/bold cyan]")
    console.print("[cyan]Created by Stew Alexander[/cyan]\n")
    
    input_file, mac_word, vendor_word = get_input_file()
    oui_manager = OUIManager()
    
    vendor_counts, vlan_data = process_vendor_devices(input_file, mac_word, vendor_word, oui_manager)
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
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
    
    # Create text summary
    create_text_summary(vendor_counts, output_dir)
    
    # Create visualizations
    create_visualizations(vendor_counts, vlan_data)
    
    # Create CSV file
    make_csv(input_file)
    
    console.print("\n[green]Analysis complete![/green]")
    console.print(f"[cyan]Total devices analyzed: {total_devices}[/cyan]")
    console.print("\n[yellow]Output files have been created in the 'output' directory:[/yellow]")
    console.print("  • vendor_distribution.html (Interactive dashboard with vendor and VLAN analysis)")
    console.print(f"  • {os.path.splitext(os.path.basename(input_file))[0]}-Devices.csv (Detailed device list)")
    console.print("  • vendor_summary.txt (Plain text summary of vendor distribution)")

if __name__ == "__main__":
    main()
