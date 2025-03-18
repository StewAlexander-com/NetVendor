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
from rich import print as rprint
from rich.console import Console
from rich.table import Table
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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import hashlib

console = Console()

def check_dependencies() -> None:
    """
    Check if all required Python modules are installed.
    Exits the program if any required module is missing.
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

def get_input_file() -> Tuple[str, int, int]:
    """Get the input file and determine its type."""
    if len(sys.argv) != 2:
        console.print("Usage: python3 NetVendor.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        console.print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
    
    # Determine file type based on content
    if "Internet" in first_line:
        mac_word = 3  # ARP table format
        vendor_word = 4
    elif "Mac Address" in first_line:
        mac_word = 2  # MAC address table format
        vendor_word = 3
    else:
        mac_word = 1  # Default
        vendor_word = 2
    
    return input_file, mac_word, vendor_word

class OUIManager:
    """Manages OUI lookups and caching."""
    def __init__(self):
        # Create output/data directory if it doesn't exist
        self.output_dir = Path("output")
        self.data_dir = self.output_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.data_dir / "oui_cache.json"
        self.failed_lookups_file = self.data_dir / "failed_lookups.json"
        self.processed_files_file = self.data_dir / "processed_files.json"
        self.cache = {}
        self.failed_lookups = set()
        self.processed_files = {}
        self.pending_saves = 0
        self.max_pending_saves = 50
        self.last_api_call = 0
        self.min_api_interval = 2.0
        self.api_services = [
            {
                'name': 'macvendors',
                'url': 'https://api.macvendors.com/{oui}',
                'headers': {},
                'rate_limit': 2.0,  # 2 seconds between requests
                'last_call': 0
            },
            {
                'name': 'maclookup',
                'url': 'https://api.maclookup.app/v2/macs/{oui}',
                'headers': {},
                'rate_limit': 1.0,  # 1 second between requests
                'last_call': 0
            }
        ]
        self.current_service_index = 0
        self.load_cache()
        self.load_failed_lookups()
        self.load_processed_files()
    
    def load_processed_files(self):
        """Load information about previously processed files."""
        if self.processed_files_file.exists():
            try:
                with open(self.processed_files_file, 'r') as f:
                    self.processed_files = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.processed_files = {}

    def save_processed_files(self):
        """Save information about processed files."""
        with open(self.processed_files_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    def get_file_metadata(self, file_path: str) -> dict:
        """Get file metadata including size, modification time, and content hash."""
        file_stat = os.stat(file_path)
        
        # Calculate hash of first and last 1MB of file
        # This is faster than hashing the entire file and still catches most changes
        with open(file_path, 'rb') as f:
            # Read first 1MB
            start_content = f.read(1024 * 1024)
            
            # Seek to last 1MB
            f.seek(max(0, file_stat.st_size - (1024 * 1024)))
            end_content = f.read()
            
            # Create hash of both parts
            content_hash = hashlib.md5(start_content + end_content).hexdigest()
        
        return {
            'size': file_stat.st_size,
            'mtime': file_stat.st_mtime,
            'hash': content_hash
        }

    def has_file_changed(self, file_path: str) -> bool:
        """Check if a file has changed since last processing."""
        current_metadata = self.get_file_metadata(file_path)
        
        if file_path not in self.processed_files:
            return True
        
        stored_metadata = self.processed_files[file_path]
        return (current_metadata['size'] != stored_metadata['size'] or
                current_metadata['mtime'] != stored_metadata['mtime'] or
                current_metadata['hash'] != stored_metadata['hash'])

    def update_file_metadata(self, file_path: str):
        """Update stored metadata for a processed file."""
        self.processed_files[file_path] = self.get_file_metadata(file_path)
        self.save_processed_files()

    def load_failed_lookups(self):
        """Load previously failed lookups to avoid retrying them."""
        if self.failed_lookups_file.exists():
            try:
                with open(self.failed_lookups_file, 'r') as f:
                    self.failed_lookups = set(json.load(f))
            except (json.JSONDecodeError, IOError):
                self.failed_lookups = set()

    def save_failed_lookups(self):
        """Save failed lookups to avoid retrying them in future runs."""
        with open(self.failed_lookups_file, 'w') as f:
            json.dump(list(self.failed_lookups), f)

    def load_cache(self):
        """Load OUI cache from file and normalize MAC addresses."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    raw_cache = json.load(f)
                    # Normalize cache entries
                    self.cache = {
                        self._normalize_mac(mac): vendor 
                        for mac, vendor in raw_cache.items()
                    }
            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Warning: Could not load cache file ({e}), creating new cache[/yellow]")
                self.cache = {}
    
    def save_cache(self, force=False):
        """Save OUI cache to file if enough changes have accumulated or force is True."""
        if not force and self.pending_saves < self.max_pending_saves:
            self.pending_saves += 1
            return
        
        # Reset pending saves counter
        self.pending_saves = 0
        
        # Remove any duplicate vendor entries before saving
        unique_cache = {}
        for mac, vendor in self.cache.items():
            if vendor not in unique_cache.values():
                unique_cache[mac] = vendor
        
        with open(self.cache_file, 'w') as f:
            json.dump(unique_cache, f, sort_keys=True, indent=2)
    
    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address format."""
        # Remove any separators and convert to uppercase
        mac = re.sub(r'[.:-]', '', mac.upper())
        # Keep only first 6 characters (OUI portion)
        return mac[:6]
    
    def _validate_mac(self, mac: str) -> bool:
        """Validate MAC address format."""
        # Check if it's a valid hex string of correct length
        return bool(re.match(r'^[0-9A-F]{6}', self._normalize_mac(mac)))
    
    def _rate_limit(self, service):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last_call = current_time - service['last_call']
        if time_since_last_call < service['rate_limit']:
            sleep_time = service['rate_limit'] - time_since_last_call
            time.sleep(sleep_time)
        service['last_call'] = time.time()

    def lookup_vendor(self, mac: str) -> str:
        """Look up vendor for MAC address using multiple services."""
        if not self._validate_mac(mac):
            return "Unknown"
            
        oui = self._normalize_mac(mac)
        
        # Check cache first
        if oui in self.cache:
            return self.cache[oui]
        
        # Check if this OUI previously failed lookup
        if oui in self.failed_lookups:
            return "Unknown"

        # Try each service in rotation
        original_service_index = self.current_service_index
        retries = 0
        max_retries = len(self.api_services) * 2

        while retries < max_retries:
            service = self.api_services[self.current_service_index]
            
            try:
                self._rate_limit(service)
                url = service['url'].format(oui=oui)
                response = requests.get(url, headers=service['headers'], timeout=5)
                
                if response.status_code == 200:
                    if service['name'] == 'maclookup':
                        data = response.json()
                        vendor = data.get('company', 'Unknown')
                    else:
                        vendor = response.text

                    if vendor and vendor != "Unknown":
                        self.cache[oui] = vendor
                        self.save_cache()
                        return vendor
                        
                elif response.status_code == 429:
                    # Don't print rate limit messages during normal operation
                    service['rate_limit'] *= 1.5
                    
                elif response.status_code == 404:
                    self.failed_lookups.add(oui)
                    self.save_failed_lookups()
                    return "Unknown"

            except (requests.RequestException, json.JSONDecodeError) as e:
                pass  # Silently handle errors and try next service

            self.current_service_index = (self.current_service_index + 1) % len(self.api_services)
            retries += 1

            if self.current_service_index == original_service_index:
                time.sleep(1)

        self.failed_lookups.add(oui)
        self.save_failed_lookups()
        return "Unknown"

    def batch_lookup_vendors(self, macs: List[str], progress: Progress = None) -> Dict[str, str]:
        """Process MAC addresses in batch, using cache when available."""
        results = {}
        unknown_macs = []
        
        # First check cache for all MACs
        for mac in macs:
            if not self._validate_mac(mac):
                results[mac] = "Unknown"
                continue
                
            oui = self._normalize_mac(mac)
            if oui in self.cache:
                results[mac] = self.cache[oui]
            elif oui in self.failed_lookups:
                results[mac] = "Unknown"
            else:
                unknown_macs.append(mac)
        
        # Only create progress task if there are actually unknown MACs to look up
        if unknown_macs and progress:
            task_id = progress.add_task(
                f"[cyan]Looking up vendors for {len(unknown_macs)} MAC addresses...", 
                total=len(unknown_macs)
            )
            
            # Look up unknown MACs one at a time
            for mac in unknown_macs:
                results[mac] = self.lookup_vendor(mac)
                progress.advance(task_id)
        
        return results

    def cleanup_cache(self) -> Tuple[int, int]:
        """Clean up the OUI cache for efficiency."""
        console.print("\n[yellow]Starting OUI cache cleanup...[/yellow]")
        original_count = len(self.cache)
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            cleanup_task = progress.add_task("[cyan]Cleaning up cache...", total=100)
            
            # Step 1: Normalize MAC addresses
            progress.update(cleanup_task, description="[cyan]Normalizing MAC addresses...", completed=20)
            normalized_cache = {}
            for mac, vendor in self.cache.items():
                if self._validate_mac(mac):
                    normalized_mac = self._normalize_mac(mac)
                    normalized_cache[normalized_mac] = vendor
            
            # Step 2: Standardize vendor names
            progress.update(cleanup_task, description="[cyan]Standardizing vendor names...", completed=40)
            vendor_standardized = {
                mac: vendor.replace(', Inc.', '').replace(' Inc.', '').replace(' Corporation', '').strip()
                for mac, vendor in normalized_cache.items()
            }
            
            # Step 3: Remove duplicates
            progress.update(cleanup_task, description="[cyan]Removing duplicates...", completed=60)
            unique_entries = {}
            vendor_counts = {}
            for mac, vendor in vendor_standardized.items():
                if vendor not in vendor_counts:
                    vendor_counts[vendor] = 0
                vendor_counts[vendor] += 1
                unique_entries[mac] = vendor
            
            # Step 4: Update cache with cleaned data
            progress.update(cleanup_task, description="[cyan]Updating cache...", completed=80)
            self.cache = unique_entries
            self.save_cache()
            
            # Complete progress
            progress.update(cleanup_task, completed=100)
        
        # Print summary
        cleaned_count = len(self.cache)
        duplicates_removed = original_count - cleaned_count
        
        if original_count > 0:
            console.print("\n[green]Cache cleanup completed![/green]")
            console.print(f"\n[yellow]Cleanup Summary:[/yellow]")
            console.print(f"• Original entries: {original_count}")
            console.print(f"• Cleaned entries: {cleaned_count}")
            console.print(f"• Duplicates removed: {duplicates_removed}")
            console.print("\n[yellow]Vendor Distribution:[/yellow]")
            for vendor, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                console.print(f"• {vendor}: {count} entries")
        else:
            console.print("\n[yellow]Starting with fresh cache - no cleanup needed[/yellow]")
        
        return original_count, cleaned_count

def create_visualizations(vendor_counts: Dict[str, int], vlan_data: List[str]) -> None:
    """Create interactive visualizations of vendor and VLAN distributions."""
    console.print("[cyan]Creating visualizations...[/cyan]")
    
    # Process VLAN data with progress tracking
    vlan_vendor_data = {}  # VLAN -> {vendor: count}
    vendor_vlan_data = {}  # Vendor -> {vlan: count}
    vlan_total_devices = Counter()  # Total devices per VLAN
    vlan_unique_vendors = Counter()  # Unique vendors per VLAN
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        # Step 1: Process VLAN data
        vlan_task = progress.add_task("[cyan]Processing VLAN data...", total=len(vlan_data))
        
        for line in vlan_data:
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) >= 3:  # Format is "MAC VENDOR VLAN"
                try:
                    mac = parts[0]
                    vendor_parts = parts[1:-1]
                    vendor = ' '.join(vendor_parts)
                    vlan = parts[-1]
                    
                    if not vlan.isdigit():
                        continue
                    
                    # Update VLAN vendor distribution
                    if vlan not in vlan_vendor_data:
                        vlan_vendor_data[vlan] = Counter()
                    vlan_vendor_data[vlan][vendor] += 1
                    
                    # Update vendor VLAN distribution
                    if vendor not in vendor_vlan_data:
                        vendor_vlan_data[vendor] = Counter()
                    vendor_vlan_data[vendor][vlan] += 1
                    
                    # Update VLAN statistics
                    vlan_total_devices[vlan] += 1
                    vlan_unique_vendors[vlan] = len(vlan_vendor_data[vlan])
                    
                except (IndexError, ValueError):
                    continue
            
            progress.advance(vlan_task)
        
        # Step 2: Create vendor distribution chart (unchanged)
        chart1_task = progress.add_task("[cyan]Creating vendor distribution chart...", total=100)
        
        # Create pie chart for overall vendor distribution
        fig1 = go.Figure()
        sorted_vendors = sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)
        labels = [v[0] for v in sorted_vendors]
        values = [v[1] for v in sorted_vendors]
        total_devices = sum(vendor_counts.values())
        
        # Enhanced hover text with more details
        hover_text = [
            f"Vendor: {label}<br>" +
            f"Device Count: {value:,} devices<br>" +
            f"Percentage: {(value/total_devices)*100:.1f}%<br>" +
            f"Present in {len(vendor_vlan_data.get(label, []))} VLANs<br>" +
            f"Most Common VLAN: {max(vendor_vlan_data.get(label, {0: 0}).items(), key=lambda x: x[1])[0] if vendor_vlan_data.get(label) else 'N/A'}<br>" +
            f"Max Devices in a VLAN: {max(vendor_vlan_data.get(label, {0: 0}).values()) if vendor_vlan_data.get(label) else 0}"
            for label, value in zip(labels, values)
        ]
        
        legend_labels = [f"{label} ({value:,})" for label, value in zip(labels, values)]
        
        fig1.add_trace(
            go.Pie(
                labels=legend_labels,
                values=values,
                hovertemplate="%{customdata}<br><extra></extra>",
                customdata=hover_text,
                textinfo='label',
                textposition='outside',
                hole=0.3
            )
        )
        
        # Update fig1 layout for pie chart
        fig1.update_layout(
            title=None,
            showlegend=True,
            autosize=True,
            legend=dict(
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.15,  # Increased spacing for legend
                font=dict(size=12),
                itemsizing='constant'
            ),
            margin=dict(
                l=50,
                r=300,  # Increased right margin for legend
                t=50,
                b=50,
                autoexpand=True
            )
        )
        
        # Update trace for better label visibility
        fig1.update_traces(
            textfont_size=11,  # Slightly smaller font for better fit
            textposition='outside',
            pull=[0.03] * len(values),  # Slightly reduced pull for tighter layout
            rotation=90  # Keep starting at 12 o'clock position
        )
        
        progress.update(chart1_task, completed=100)
        
        # Step 3: Create enhanced VLAN analysis charts
        chart2_task = progress.add_task("[cyan]Creating VLAN analysis charts...", total=100)
        
        # Create subplot figure with 2x2 layout
        fig2 = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "VLAN Device Count",
                "Unique Vendors per VLAN",
                "Vendor Distribution per VLAN",
                "Top Vendors per VLAN"
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1,
            row_heights=[0.4, 0.6]
        )
        
        progress.update(chart2_task, completed=20)
        
        # Sort VLANs numerically
        sorted_vlans = sorted(vlan_vendor_data.keys(), key=lambda x: int(x))
        
        # 1. VLAN Device Count Bar Chart
        vlan_total_counts = [vlan_total_devices[vlan] for vlan in sorted_vlans]
        fig2.add_trace(
            go.Bar(
                x=[f"VLAN {v}" for v in sorted_vlans],
                y=vlan_total_counts,
                name="Total Devices",
                hovertemplate="VLAN: %{x}<br>Devices: %{y}<extra></extra>",
                marker_color='rgb(55, 83, 109)'
            ),
            row=1, col=1
        )
        
        # 2. Unique Vendors per VLAN
        unique_vendor_counts = [vlan_unique_vendors[vlan] for vlan in sorted_vlans]
        fig2.add_trace(
            go.Bar(
                x=[f"VLAN {v}" for v in sorted_vlans],
                y=unique_vendor_counts,
                name="Unique Vendors",
                hovertemplate="VLAN: %{x}<br>Unique Vendors: %{y}<extra></extra>",
                marker_color='rgb(26, 118, 255)'
            ),
            row=1, col=2
        )
        
        progress.update(chart2_task, completed=40)
        
        # 3. Vendor Distribution Heatmap
        # Get top vendors for better visualization
        top_vendors = [v[0] for v in sorted_vendors[:20]]  # Show top 20 vendors
        heatmap_data = []
        for vendor in top_vendors:
            row = []
            for vlan in sorted_vlans:
                count = vendor_vlan_data.get(vendor, {}).get(vlan, 0)
                row.append(count)
            heatmap_data.append(row)
        
        fig2.add_trace(
            go.Heatmap(
                z=heatmap_data,
                x=[f"VLAN {v}" for v in sorted_vlans],
                y=top_vendors,
                colorscale='Viridis',
                showscale=True,
                hovertemplate="VLAN: %{x}<br>Vendor: %{y}<br>Devices: %{z}<extra></extra>"
            ),
            row=2, col=1
        )
        
        progress.update(chart2_task, completed=60)
        
        # 4. Top Vendors per VLAN Stacked Bar Chart
        top_5_vendors = [v[0] for v in sorted_vendors[:5]]
        stacked_data = []
        
        for vendor in top_5_vendors:
            vendor_counts = []
            for vlan in sorted_vlans:
                count = vendor_vlan_data.get(vendor, {}).get(vlan, 0)
                vendor_counts.append(count)
            
            stacked_data.append(
                go.Bar(
                    name=vendor,
                    x=[f"VLAN {v}" for v in sorted_vlans],
                    y=vendor_counts,
                    hovertemplate="VLAN: %{x}<br>Vendor: " + vendor + "<br>Devices: %{y}<extra></extra>"
                )
            )
        
        for trace in stacked_data:
            fig2.add_trace(trace, row=2, col=2)
        
        progress.update(chart2_task, completed=80)
        
        # Update layout for all subplots
        fig2.update_layout(
            autosize=True,
            showlegend=True,
            barmode='stack',
            height=1000,  # Increased minimum height
            grid=dict(
                rows=2,
                columns=2,
                pattern='independent',
                roworder='top to bottom',
                ygap=0.2,  # Increased vertical gap between plots
                xgap=0.1   # Horizontal gap between plots
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,  # Moved legend down
                xanchor="center",
                x=0.5
            ),
            template="plotly_white",
            margin=dict(
                l=80,
                r=80,
                t=100,  # Increased top margin
                b=150,  # Increased bottom margin for legend
                autoexpand=True
            )
        )
        
        # Update axes for better readability
        for i in range(1, 5):
            fig2.update_xaxes(tickangle=45, row=(i+1)//2, col=(i-1)%2+1)
        
        progress.update(chart2_task, completed=100)
        
        # Step 4: Save visualizations
        save_task = progress.add_task("[cyan]Saving visualizations...", total=100)
        
        # Create output directory
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        progress.update(save_task, completed=20)
        
        # Write HTML file with enhanced styling
        with open(os.path.join(output_dir, "vendor_distribution.html"), 'w') as f:
            f.write("""
            <html>
            <head>
                <title>Network Device Analysis</title>
                <style>
                    body { 
                        max-width: 100%; 
                        margin: 0; 
                        padding: 0; 
                        font-family: Arial, sans-serif;
                        background-color: #f5f5f5;
                        min-height: 100vh;
                    }
                    .page-nav {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: white;
                        padding: 15px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        z-index: 1000;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .page-nav a {
                        margin: 0 15px;
                        text-decoration: none;
                        color: #333;
                        font-weight: bold;
                        padding: 8px 15px;
                        border-radius: 3px;
                        transition: background-color 0.3s;
                        display: inline-block;
                    }
                    .page-nav a:hover {
                        background-color: #f0f0f0;
                    }
                    .page-nav a.active {
                        background-color: #f0f0f0;
                    }
                    .page { 
                        display: none;
                        padding: 80px 40px 40px 40px;
                        margin: 0;
                        min-height: calc(100vh - 120px);
                    }
                    .page.active { 
                        display: block;
                    }
                    h1 { 
                        color: #2c3e50; 
                        text-align: center; 
                        margin: 0 0 30px 0;
                        padding-top: 20px;
                        font-size: 2.5em;
                    }
                    .chart-container { 
                        margin: 30px auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    .description {
                        color: #666;
                        text-align: center;
                        margin: 0 auto 30px auto;
                        font-size: 1.2em;
                        line-height: 1.6;
                        max-width: 900px;
                    }
                    #page1 .chart-container {
                        max-width: 1800px;
                        min-height: 800px;
                    }
                    #page2 .chart-container {
                        max-width: 1800px;
                        min-height: 1200px;
                    }
                </style>
                <script>
                    function showPage(pageNum) {
                        // Remove active class from all pages and nav links
                        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
                        document.querySelectorAll('.page-nav a').forEach(link => link.classList.remove('active'));
                        
                        // Add active class to selected page and nav link
                        document.getElementById('page' + pageNum).classList.add('active');
                        document.querySelector('.page-nav a[data-page="' + pageNum + '"]').classList.add('active');
                        
                        // Trigger resize event to update chart sizes
                        window.dispatchEvent(new Event('resize'));
                    }
                    
                    window.onload = () => {
                        showPage(1);
                        
                        // Make charts responsive
                        function updateChartSizes() {
                            const containers = document.querySelectorAll('.chart-container');
                            containers.forEach(container => {
                                const viewportWidth = window.innerWidth;
                                const viewportHeight = window.innerHeight;
                                
                                const charts = container.getElementsByClassName('plotly-graph-div');
                                Array.from(charts).forEach(chart => {
                                    // Check if this is the VLAN analysis chart
                                    const hasSubplots = chart.layout && chart.layout.grid && chart.layout.grid.rows > 1;
                                    
                                    let width, height;
                                    if (hasSubplots) {
                                        // VLAN analysis charts
                                        width = Math.min(viewportWidth * 0.9, 1800);
                                        height = Math.min(viewportHeight * 1.2, 1200);
                                    } else {
                                        // Pie chart
                                        width = Math.min(viewportWidth * 0.85, 1600);
                                        height = Math.min(viewportHeight * 0.8, 900);
                                    }
                                    
                                    // Ensure minimum dimensions
                                    width = Math.max(width, 1000);
                                    height = Math.max(height, hasSubplots ? 1000 : 800);
                                    
                                    Plotly.relayout(chart, {
                                        width: width,
                                        height: height,
                                        'autosize': true
                                    });
                                });
                            });
                        }
                        
                        // Update sizes on load and resize
                        updateChartSizes();
                        window.addEventListener('resize', updateChartSizes);
                    }
                </script>
            </head>
            <body>
                <h1>Network Device Analysis Dashboard</h1>
                <div class="page-nav">
                    <a href="#" data-page="1" onclick="showPage(1); return false;">Vendor Distribution</a>
                    <a href="#" data-page="2" onclick="showPage(2); return false;">VLAN Analysis</a>
                </div>
                <div id="page1" class="page">
                    <div class="description">
                        Overall distribution of network devices across different vendors.
                        Hover over segments for detailed information about each vendor.
                    </div>
                    <div class="chart-container">
            """)
            
            progress.update(save_task, completed=40)
            f.write(fig1.to_html(full_html=False, include_plotlyjs=True))
            
            progress.update(save_task, completed=70)
            f.write("""
                    </div>
                </div>
                <div id="page2" class="page">
                    <div class="description">
                        Comprehensive VLAN analysis showing device distribution, vendor diversity,
                        and relationships between VLANs and vendors. Use the interactive features
                        to explore specific VLANs and vendors.
                    </div>
                    <div class="chart-container">
            """)
            f.write(fig2.to_html(full_html=False, include_plotlyjs=False))
            f.write('</div></div></body></html>')
            
            progress.update(save_task, completed=100)

def process_vendor_devices(ip_arp_file: str, mac_word: int, vendor_word: int, oui_manager: OUIManager) -> Tuple[Dict[str, int], List[str]]:
    """Process the input file and count devices per vendor."""
    vendor_counts = {}
    vlan_data = []
    mac_batch = []
    mac_to_vlan = {}
    batch_size = 10
    chunk_size = 1024 * 1024  # 1MB chunks for memory efficiency
    
    # Check if file has changed since last processing
    file_changed = oui_manager.has_file_changed(ip_arp_file)
    if not file_changed:
        console.print("[green]File hasn't changed since last run. Using cached results...[/green]")
    
    # Pre-compile patterns
    cisco_mac_pattern = re.compile(r'([0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}')
    standard_mac_pattern = re.compile(r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}')
    
    with open(ip_arp_file, 'r') as f:
        # Get file size for progress tracking
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)
        
        # Determine file type from first line
        first_line = f.readline().strip()
        is_mac_table = "Mac Address" in first_line
        start_line = 2 if is_mac_table else 0
        
        # Skip header lines if needed
        if start_line > 0:
            f.readline()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            read_task = progress.add_task("[cyan]Reading MAC addresses...", total=file_size)
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                lines = chunk.splitlines()
                
                if not chunk.endswith('\n') and len(lines) > 1:
                    f.seek(f.tell() - len(lines[-1]))
                    lines = lines[:-1]
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    parts = line.split()
                    if len(parts) < max(mac_word, vendor_word):
                        continue
                    
                    if is_mac_table:
                        if len(parts) >= 4:
                            mac = parts[1].replace('.', ':')
                            vlan = parts[0].strip()
                            normalized_mac = oui_manager._normalize_mac(mac)
                            
                            if normalized_mac in oui_manager.cache:
                                vendor = oui_manager.cache[normalized_mac]
                                if vendor != "Unknown":
                                    vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                                vlan_data.append(f"{mac} {vendor} {vlan}")
                            elif file_changed:
                                mac_batch.append(mac)
                                mac_to_vlan[mac] = vlan
                    else:
                        mac = parts[mac_word].replace('.', ':')
                        vlan = parts[-1].replace('Vlan', '') if 'Vlan' in parts[-1] else 'Unknown'
                        normalized_mac = oui_manager._normalize_mac(mac)
                        
                        if normalized_mac in oui_manager.cache:
                            vendor = oui_manager.cache[normalized_mac]
                            if vendor != "Unknown":
                                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                            vlan_data.append(f"{mac} {vendor} {vlan}")
                        elif file_changed:
                            mac_batch.append(mac)
                            mac_to_vlan[mac] = vlan
                    
                    # Process batch if it's full and file has changed
                    if file_changed and len(mac_batch) >= batch_size:
                        vendor_results = oui_manager.batch_lookup_vendors(mac_batch, progress)
                        for mac, vendor in vendor_results.items():
                            if vendor != "Unknown":
                                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                            vlan = mac_to_vlan[mac]
                            vlan_data.append(f"{mac} {vendor} {vlan}")
                        mac_batch = []
                        mac_to_vlan = {}
                
                progress.advance(read_task, len(chunk))
            
            # Process any remaining MACs in the last batch
            if file_changed and mac_batch:
                vendor_results = oui_manager.batch_lookup_vendors(mac_batch, progress)
                for mac, vendor in vendor_results.items():
                    if vendor != "Unknown":
                        vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                    vlan = mac_to_vlan[mac]
                    vlan_data.append(f"{mac} {vendor} {vlan}")
    
    # Update file metadata after successful processing
    if file_changed:
        oui_manager.update_file_metadata(ip_arp_file)
    
    return vendor_counts, vlan_data

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

def make_csv(file: str, oui_manager: OUIManager) -> None:
    """Create a CSV file with device information."""
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_file = os.path.join(output_dir, f"{base_name}-Devices.csv")
    
    # Pre-compile patterns
    cisco_mac_pattern = re.compile(r'([0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}')
    vlan_pattern = re.compile(r'Vlan(\d+)')
    
    # Process in chunks for memory efficiency
    chunk_size = 1024 * 1024  # 1MB chunks
    
    # Check if file has changed since last processing
    file_changed = oui_manager.has_file_changed(file)
    
    # Count total lines first for progress tracking
    total_lines = sum(1 for _ in open(file, 'r'))
    lines_processed = 0
    
    # Store MACs that need lookup
    mac_batch = []
    csv_rows = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        read_task = progress.add_task("[cyan]Reading device data...", total=total_lines)
        
        with open(file, 'r') as infile:
            # Determine file format from first line
            first_line = infile.readline().strip()
            is_mac_table = "Mac Address" in first_line
            lines_processed += 1
            progress.update(read_task, completed=lines_processed)
            
            # Skip header line for MAC table format
            if is_mac_table:
                infile.readline()  # Skip separator line
                lines_processed += 1
                progress.update(read_task, completed=lines_processed)
            
            while True:
                chunk = infile.read(chunk_size)
                if not chunk:
                    break
                
                lines = chunk.splitlines()
                
                # Handle partial last line
                if not chunk.endswith('\n') and len(lines) > 1:
                    infile.seek(infile.tell() - len(lines[-1]))
                    lines = lines[:-1]
                
                for line in lines:
                    if not line.strip() or line.startswith('#'):
                        lines_processed += 1
                        progress.update(read_task, completed=lines_processed)
                        continue
                    
                    parts = line.split()
                    
                    if is_mac_table and len(parts) >= 4:
                        # MAC table format: VLAN MAC TYPE PORT
                        ip = "N/A"
                        mac = parts[1].replace('.', ':')
                        vlan = parts[0].strip()
                        normalized_mac = oui_manager._normalize_mac(mac)
                        
                        if normalized_mac in oui_manager.cache:
                            vendor = oui_manager.cache[normalized_mac]
                        else:
                            if file_changed:
                                mac_batch.append(mac)
                            vendor = "Unknown"  # Temporary value
                        
                        csv_rows.append([ip, mac, vlan, vendor])
                        
                    elif "Internet" in line and len(parts) >= 6:
                        # ARP table format
                        ip = parts[1]
                        mac = parts[3].replace('.', ':')
                        vlan_match = vlan_pattern.search(parts[5])
                        vlan = vlan_match.group(1) if vlan_match else parts[5].replace('Vlan', '')
                        normalized_mac = oui_manager._normalize_mac(mac)
                        
                        if normalized_mac in oui_manager.cache:
                            vendor = oui_manager.cache[normalized_mac]
                        else:
                            if file_changed:
                                mac_batch.append(mac)
                            vendor = "Unknown"  # Temporary value
                        
                        csv_rows.append([ip, mac, vlan, vendor])
                    
                    lines_processed += 1
                    progress.update(read_task, completed=min(lines_processed, total_lines))
        
        # Look up any new MACs in batch
        if mac_batch and file_changed:
            lookup_task = progress.add_task("[cyan]Looking up new vendors...", total=len(mac_batch))
            vendor_results = oui_manager.batch_lookup_vendors(mac_batch, progress)
            
            # Update CSV rows with vendor results
            mac_to_vendor = {mac: vendor for mac, vendor in vendor_results.items()}
            for row in csv_rows:
                mac = row[1]
                if mac in mac_to_vendor:
                    row[3] = mac_to_vendor[mac]
            
            progress.update(lookup_task, completed=len(mac_batch))
        
        # Write CSV file
        write_task = progress.add_task("[cyan]Writing CSV file...", total=len(csv_rows))
        with open(output_file, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['IP Address', 'MAC Address', 'VLAN', 'Vendor'])
            for row in csv_rows:
                writer.writerow(row)
                progress.advance(write_task)

def main():
    """Main function."""
    check_dependencies()
    console.print("\n[bold cyan]NetVendor - Network Device Vendor Analysis[/bold cyan]")
    console.print("=" * 60)

    # Initialize OUI manager and clean cache
    oui_manager = OUIManager()
    console.print("\n[yellow]Initializing...[/yellow]")
    original_count, cleaned_count = oui_manager.cleanup_cache()
    
    # Get input file and process
    input_file, mac_word, vendor_word = get_input_file()
    if not input_file:
        return
    
    console.print("\n[yellow]Processing network data...[/yellow]")
    
    # Process vendor devices with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        vendor_counts, vlan_data = process_vendor_devices(input_file, mac_word, vendor_word, oui_manager)
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    console.print("\n[yellow]Generating reports...[/yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        # Create and display results table
        table_task = progress.add_task("[cyan]Creating summary table...", total=100)
        
        table = Table(
            title="Network Device Vendor Summary",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("Vendor", style="cyan", no_wrap=True)
        table.add_column("Count", style="magenta", justify="right")
        table.add_column("Percentage", style="green", justify="right")
        
        total_devices = sum(vendor_counts.values())
        for vendor, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_devices) * 100
            table.add_row(vendor, str(count), f"{percentage:.1f}%")
        
        progress.update(table_task, completed=100)
        console.print("\n")
        console.print(table)
        
        # Create text summary
        summary_task = progress.add_task("[cyan]Creating text summary...", total=100)
        create_text_summary(vendor_counts, output_dir)
        progress.update(summary_task, completed=100)
        
        # Create visualizations
        viz_task = progress.add_task("[cyan]Creating visualizations...", total=100)
        create_visualizations(vendor_counts, vlan_data)
        progress.update(viz_task, completed=100)
        
        # Create CSV file
        csv_task = progress.add_task("[cyan]Creating device CSV file...", total=100)
        make_csv(input_file, oui_manager)
        progress.update(csv_task, completed=100)
    
    console.print("\n[bold green]Analysis complete![/bold green]")
    console.print(f"[cyan]Total devices analyzed: {total_devices:,}[/cyan]")
    console.print("\n[yellow]Output files have been created in the 'output' directory:[/yellow]")
    console.print("  • [blue]vendor_distribution.html[/blue] (Interactive dashboard)")
    console.print(f"  • [blue]{os.path.splitext(os.path.basename(input_file))[0]}-Devices.csv[/blue] (Device list)")
    console.print("  • [blue]vendor_summary.txt[/blue] (Text summary)")

if __name__ == "__main__":
    main()
