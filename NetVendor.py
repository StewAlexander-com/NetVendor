#!/usr/bin/env python3

"""
NetVendor - Network Device Analysis Tool

Processes network device data through several stages:
1. Reads MAC/ARP tables in chunks to handle large files efficiently
2. Uses a caching system to avoid redundant vendor lookups
3. Maintains file state to skip unchanged files
4. Generates visualizations using a multi-step process:
   - Processes raw data into vendor counts
   - Creates interactive charts with plotly
   - Combines charts into a responsive HTML dashboard
5. For MAC address tables with port information:
   - Creates port-based device analysis
   - Generates per-port VLAN and device statistics

The script adapts to different input formats by analyzing the first line
and adjusts its parsing strategy accordingly.
"""

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
from typing import List, Set, Dict, Tuple, Optional
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
from collections import defaultdict

console = Console()

def check_dependencies() -> None:
    """
    Validates required modules before script execution to prevent runtime failures.
    
    Uses __import__ for dynamic module checking, allowing the script to fail early
    if dependencies are missing. This prevents cryptic errors later in execution
    when modules are actually needed.
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
    Supports formats: 
    - 1234.5678.9abc
    - 12:34:56:78:9a:bc
    - 12-34-56-78-9a-bc
    """
    # Remove separators and convert to lowercase
    mac = mac.lower().replace(':', '').replace('.', '').replace('-', '')
    
    # Check if it's a 12-character hex string
    if len(mac) != 12:
        return False
    
    try:
        int(mac, 16)  # Try to convert to hex
        return True
    except ValueError:
        return False

def is_mac_address_table(line: str) -> bool:
    """
    Check if a line is from a MAC address table.
    Returns True if the line contains a VLAN number followed by a MAC address.
    """
    words = line.strip().split()
    if len(words) < 2:
        return False
    
    # Check if first word is a VLAN number
    try:
        vlan = int(words[0])
        if not (1 <= vlan <= 4094):  # Valid VLAN range
            return False
    except ValueError:
        return False
    
    # Check if second word is a MAC address
    return is_mac_address(words[1])

def parse_port_info(line: str) -> Optional[str]:
    """
    Extract port information from a line.
    Returns the port identifier if found, None otherwise.
    
    Handles:
    - MAC address table format (e.g., Gi1/0/1, Fa1/0/1)
    - ARP table format (no port information)
    """
    # Skip ARP table format (contains "Internet" and "ARPA")
    if "Internet" in line and "ARPA" in line:
        return None
    
    words = line.strip().split()
    if len(words) < 4:
        return None
    
    # Port is typically the last field
    port = words[-1]
    
    # Common port formats: Gi1/0/1, Fa1/0/1, Te1/1, Eth1/1, etc.
    if any(port.startswith(prefix) for prefix in ['Gi', 'Fa', 'Te', 'Eth']):
        return port
    
    return None

def get_input_file() -> Tuple[str, int, int]:
    """
    Determines input file format and column positions dynamically.
    
    Analyzes the first line of input to detect file type:
    - "Internet" -> ARP table (MAC in col 4, vendor in col 5)
    - "Mac Address" -> MAC table (MAC in col 2, vendor in col 3)
    - Other -> Default format (MAC in col 1, vendor in col 2)
    
    This adaptive parsing allows the script to handle various network device
    output formats without requiring user configuration.
    """
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
        mac_word = 4  # ARP table format (MAC is in 4th column)
        vendor_word = 5
    elif "Mac Address" in first_line:
        mac_word = 2  # MAC address table format
        vendor_word = 3
    else:
        mac_word = 1  # Default
        vendor_word = 2
    
    return input_file, mac_word, vendor_word

class OUIManager:
    """
    Manages vendor lookups with a multi-layered caching strategy:
    
    1. In-memory cache for fastest lookups
    2. File-based JSON cache for persistence
    3. Failed lookup tracking to avoid retrying bad MACs
    4. File state tracking to skip reprocessing unchanged files
    
    Uses rate limiting and service rotation for API calls:
    - Alternates between multiple vendor lookup services
    - Implements exponential backoff on rate limits
    - Batches lookups for efficiency
    
    The manager automatically creates required directories and maintains
    cache integrity through atomic writes and periodic cleanup.
    """
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

    def get_vendor(self, mac: str) -> str:
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
                results[mac] = self.get_vendor(mac)
                progress.advance(task_id)
        
        return results

    def cleanup_cache(self) -> Tuple[int, int]:
        """Clean up the OUI cache for efficiency."""
        console.print("\n[yellow]Starting OUI cache cleanup...[/yellow]")
        original_count = len(self.cache)
        cleaned_count = 0
        duplicates_removed = 0
        result = (0, 0)
        
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
            
            # Calculate results
            cleaned_count = len(self.cache)
            duplicates_removed = original_count - cleaned_count
            result = (cleaned_count, duplicates_removed)
            
        return result

@dataclass
class PortInfo:
    """
    Tracks device and VLAN information for each network port.
    
    Attributes:
        port: Physical port identifier (e.g., "Gi1/0/1")
        devices: List of (MAC, vendor, vlan) tuples
        vlan_count: Counter for VLANs seen on this port
        vendor_count: Counter for vendors seen on this port
    """
    port: str
    devices: List[Tuple[str, str, str]]  # (MAC, vendor, vlan)
    vlan_count: Counter
    vendor_count: Counter

    @property
    def total_devices(self) -> int:
        return len(self.devices)

    @property
    def total_vlans(self) -> int:
        return len(self.vlan_count)

def get_format_type(first_line: str) -> str:
    """
    Determines the specific format type of the input file.
    
    Returns:
        str: Format type ('cisco', 'hp', or 'generic')
    """
    line = first_line.lower()
    if "vlan" in line and "mac address" in line and "ports" in line:
        return "cisco"
    elif "mac address" in line:
        return "hp"
    return "generic"

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

def make_csv(input_file: Path, devices: Dict[str, Dict[str, str]], oui_manager: OUIManager) -> None:
    """
    Creates a CSV file with device information.
    
    Args:
        input_file: Path to the input file
        devices: Dictionary of device information
        oui_manager: OUI manager instance for vendor lookups
    """
    output_file = Path("output") / f"{input_file.stem}-Devices.csv"
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vlan = info.get('vlan', 'N/A')
            port = info.get('port', 'N/A')
            writer.writerow([mac, vendor, vlan, port])
    
    console.print(f"\nDevice information written to {output_file}")

def generate_port_report(input_file: Path, devices: Dict[str, Dict[str, str]], oui_manager: OUIManager) -> None:
    """
    Creates a CSV report with port-based device information.
    
    For each port, includes:
    - Port identifier
    - Total devices
    - VLANs present (comma-separated)
    - Vendors present (comma-separated)
    - Device details (MAC, vendor, VLAN)
    
    Args:
        input_file: Path to the input file
        devices: Dictionary of device information
        oui_manager: OUI manager instance for vendor lookups
    """
    # Only generate port report for MAC address tables
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
        if not is_mac_address_table(first_line):
            return

    # Initialize port data structure
    ports: Dict[str, PortInfo] = {}
    
    # Process each device and organize by port
    for mac, info in devices.items():
        port = info.get('port')
        if not port:
            continue
            
        vlan = info.get('vlan', 'Unknown')
        vendor = oui_manager.get_vendor(mac)
        
        if port not in ports:
            ports[port] = PortInfo(
                port=port,
                devices=[],
                vlan_count=Counter(),
                vendor_count=Counter()
            )
            
        ports[port].devices.append((mac, vendor, vlan))
        ports[port].vlan_count[vlan] += 1
        ports[port].vendor_count[vendor] += 1
    
    # Create output file
    output_file = input_file.stem + '-Ports.csv'
    output_path = Path('output') / output_file
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Port', 'Total Devices', 'VLANs', 'Vendors', 'Device Details'])
        
        # Sort ports for consistent output
        for port_name in sorted(ports.keys()):
            port_info = ports[port_name]
            
            # Sort VLANs and vendors for readability
            vlans = sorted(port_info.vlan_count.keys())
            vendors = sorted(port_info.vendor_count.keys())
            
            # Create detailed device list
            device_details = []
            for mac, vendor, vlan in sorted(port_info.devices):
                device_details.append(f"{mac} ({vendor}, VLAN {vlan})")
            
            writer.writerow([
                port_name,
                port_info.total_devices,
                ','.join(vlans),
                ','.join(vendors),
                ' / '.join(device_details)
            ])

def create_vendor_distribution(devices: Dict[str, Dict[str, str]], oui_manager: OUIManager, input_file: Path) -> None:
    """
    Creates interactive visualizations of vendor and VLAN distributions.
    
    Args:
        devices: Dictionary of device information
        oui_manager: OUI manager instance for vendor lookups
        input_file: Path to the input file
    """
    console.print("[cyan]Creating visualizations...[/cyan]")
    
    # Process data for visualization
    vendor_counts = Counter()
    vlan_vendor_data = defaultdict(Counter)  # VLAN -> {vendor: count}
    vendor_vlan_data = defaultdict(Counter)  # Vendor -> {vlan: count}
    vlan_total_devices = Counter()  # Total devices per VLAN
    vlan_unique_vendors = Counter()  # Unique vendors per VLAN
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        # Step 1: Process device data
        data_task = progress.add_task("[cyan]Processing device data...", total=len(devices))
        
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vlan = info.get('vlan', 'N/A')
            
            # Update counters
            vendor_counts[vendor] += 1
            vlan_vendor_data[vlan][vendor] += 1
            vendor_vlan_data[vendor][vlan] += 1
            vlan_total_devices[vlan] += 1
            vlan_unique_vendors[vlan] = len(vlan_vendor_data[vlan])
            
            progress.advance(data_task)
        
        # Step 2: Create vendor distribution chart
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
            f"Present in {len(vendor_vlan_data[label])} VLANs<br>" +
            f"Most Common VLAN: {max(vendor_vlan_data[label].items(), key=lambda x: x[1])[0] if vendor_vlan_data[label] else 'N/A'}<br>" +
            f"Max Devices in a VLAN: {max(vendor_vlan_data[label].values()) if vendor_vlan_data[label] else 0}"
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
                x=1.15,
                font=dict(size=12),
                itemsizing='constant'
            ),
            margin=dict(
                l=50,
                r=300,
                t=50,
                b=50,
                autoexpand=True
            )
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
        sorted_vlans = sorted(vlan_vendor_data.keys(), key=lambda x: str(x))
        
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
                count = vendor_vlan_data[vendor][vlan]
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
                count = vendor_vlan_data[vendor][vlan]
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
            height=1000,
            grid=dict(
                rows=2,
                columns=2,
                pattern='independent',
                roworder='top to bottom',
                ygap=0.2,
                xgap=0.1
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            template="plotly_white",
            margin=dict(
                l=80,
                r=80,
                t=100,
                b=150,
                autoexpand=True
            )
        )
        
        # Update axes for better readability
        for i in range(1, 5):
            fig2.update_xaxes(tickangle=45, row=(i+1)//2, col=(i-1)%2+1)
        
        # Step 4: Save visualizations
        save_task = progress.add_task("[cyan]Saving visualizations...", total=100)
        
        # Write HTML file with enhanced styling
        output_file = Path("output") / "vendor_distribution.html"
        with open(output_file, 'w') as f:
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
            
        console.print(f"\nVisualizations written to {output_file}")

def save_vendor_summary(devices: Dict[str, Dict[str, str]], oui_manager: OUIManager, input_file: Path) -> None:
    """
    Create a plain text summary of vendor distribution.
    
    Args:
        devices: Dictionary of device information
        oui_manager: OUI manager instance for vendor lookups
        input_file: Path to the input file
    """
    # Count vendors
    vendor_counts = Counter()
    for mac in devices:
        vendor = oui_manager.get_vendor(mac)
        vendor_counts[vendor] += 1
    
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
    output_file = Path("output") / "vendor_summary.txt"
    with open(output_file, 'w') as f:
        f.write(header)
        f.write(separator)
        f.write(column_header)
        f.write(separator.replace('-', '='))  # Double separator under headers
        for row in rows:
            f.write(row)
        f.write(separator)
    
    console.print(f"\nVendor summary written to {output_file}")

def main():
    """
    Main execution flow of the NetVendor tool.
    
    Process:
    1. Validates dependencies and input
    2. Determines input format and processing strategy
    3. Processes device data with appropriate parser
    4. Generates reports and visualizations
    """
    check_dependencies()

    # Initialize OUI manager
    oui_manager = OUIManager()
    console.print("\nInitializing...")
    original_count, cleaned_count = oui_manager.cleanup_cache()

    # Get input file and format information
    input_file_str, mac_word, vendor_word = get_input_file()
    input_file = Path(input_file_str)

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Process the input file
    devices = {}
    line_count = 0
    port_count = 0
    
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
        is_arp_table = "Internet" in first_line
        f.seek(0)  # Reset to start of file
        
        for line in f:
            line_count += 1
            words = line.strip().split()
            if len(words) >= mac_word:
                mac = words[mac_word - 1].lower()
                if is_mac_address(mac):
                    if is_arp_table:
                        # Extract VLAN from "VlanXXX" format
                        vlan = words[-1].replace('Vlan', '') if 'Vlan' in words[-1] else 'N/A'
                        port = None  # ARP tables don't have port information
                    else:
                        vlan = words[0] if is_mac_address_table(line) else 'N/A'
                        port = parse_port_info(line)
                        if port:
                            port_count += 1
                    devices[mac] = {'vlan': vlan, 'port': port if port else 'N/A'}
    
    console.print(f"\nProcessed {line_count} lines")
    if not is_arp_table:
        console.print(f"Found {port_count} port entries")
        console.print(f"Found {len(set(d['port'] for d in devices.values() if d['port'] != 'N/A'))} unique ports")
    
    # Generate reports
    make_csv(input_file, devices, oui_manager)
    
    # Only generate port report for MAC address tables
    if not is_arp_table:
        generate_port_report(input_file, devices, oui_manager)
    
    # Create vendor distribution visualization
    create_vendor_distribution(devices, oui_manager, input_file)
    
    # Save vendor summary
    save_vendor_summary(devices, oui_manager, input_file)

if __name__ == "__main__":
    main()
