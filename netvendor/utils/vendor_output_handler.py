#!/usr/bin/env python3
"""
Module for handling output generation in the NetVendor package.
This module provides functions for creating various output files:
- CSV files with device information
- Port-based reports
- Vendor distribution visualizations
- Text summaries of vendor distributions
"""

import os
import csv
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Set, Any
from collections import Counter
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from pathlib import Path
from collections import defaultdict

console = Console()

def make_csv(input_file: str, devices: Dict[str, Dict[str, str]], oui_manager) -> None:
    """
    Create a CSV file with device information.
    
    Args:
        input_file (str): Path to input file
        devices (Dict[str, Dict[str, str]]): Dictionary of devices
        oui_manager: OUI manager instance
    """
    # Create output file path
    output_file = os.path.join('output', os.path.basename(input_file).replace('.txt', '-Devices.csv'))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        for mac, info in devices.items():
            writer.writerow([
                mac,
                oui_manager.get_vendor(mac),
                info.get('vlan', ''),
                info.get('port', '')
            ])

def generate_port_report(input_file: str, devices: Dict[str, Dict[str, str]], oui_manager, is_mac_table: bool = True) -> None:
    """
    Generate a CSV report with port-based device information.
    
    Args:
        input_file (str): Path to input file
        devices (Dict[str, Dict[str, str]]): Dictionary of devices
        oui_manager: OUI manager instance
        is_mac_table (bool): Whether the data is from a MAC table
    """
    # Create output file path
    output_file = os.path.join('output', os.path.basename(input_file).replace('.txt', '-Ports.csv'))
    
    # Group devices by port
    port_data = {}
    for mac, device in devices.items():
        port = device.get('port', '')
        if port not in port_data:
            port_data[port] = {
                'total_devices': 0,
                'vlans': set(),
                'vendors': set(),
                'devices': []
            }
        
        port_info = port_data[port]
        port_info['total_devices'] += 1
        port_info['vlans'].add(device.get('vlan', ''))
        port_info['vendors'].add(oui_manager.get_vendor(mac))
        port_info['devices'].append(mac)
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Port', 'Total Devices', 'VLANs', 'Vendors', 'Devices'])
        for port, info in port_data.items():
            writer.writerow([
                port,
                info['total_devices'],
                ','.join(sorted(info['vlans'])),
                ','.join(sorted(info['vendors'])),
                ','.join(info['devices'])
            ])

def create_vendor_distribution(devices: Dict[str, Dict[str, str]], oui_manager, input_file: Path) -> None:
    """Creates interactive visualizations of vendor and VLAN distributions."""
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
        
        # 1. VLAN Device Count
        fig2.add_trace(
            go.Bar(
                x=[f"VLAN {v}" for v in sorted_vlans],
                y=[vlan_total_devices[vlan] for vlan in sorted_vlans],
                name="Total Devices",
                hovertemplate="VLAN: %{x}<br>Devices: %{y}<extra></extra>",
                marker_color='rgb(55, 83, 109)'
            ),
            row=1, col=1
        )
        
        progress.update(chart2_task, completed=40)
        
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
        
        progress.update(chart2_task, completed=60)
        
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
        
        progress.update(chart2_task, completed=80)
        
        # 4. Top Vendors per VLAN Stacked Bar Chart
        top_5_vendors = [v[0] for v in sorted_vendors[:5]]
        for vendor in top_5_vendors:
            vendor_counts = []
            for vlan in sorted_vlans:
                count = vendor_vlan_data[vendor][vlan]
                vendor_counts.append(count)
            
            fig2.add_trace(
                go.Bar(
                    name=vendor,
                    x=[f"VLAN {v}" for v in sorted_vlans],
                    y=vendor_counts,
                    hovertemplate="VLAN: %{x}<br>Vendor: " + vendor + "<br>Devices: %{y}<extra></extra>"
                ),
                row=2, col=2
            )
        
        progress.update(chart2_task, completed=100)
        
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

def save_vendor_summary(devices: Dict[str, Dict[str, str]], oui_manager, input_file: str) -> None:
    """
    Create a plain text summary of vendor distribution.
    
    Args:
        devices (Dict[str, Dict[str, str]]): Dictionary of devices
        oui_manager: OUI manager instance
        input_file (str): Path to input file
    """
    # Create output file path
    output_file = os.path.join('output', 'vendor_summary.txt')
    
    # Count vendors
    vendor_counts = Counter(oui_manager.get_vendor(mac) for mac in devices.keys())
    total_devices = len(devices)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write summary
    with open(output_file, 'w') as f:
        f.write(f"Vendor Distribution Summary\n")
        f.write(f"=========================\n\n")
        f.write(f"Total Devices: {total_devices}\n\n")
        f.write("Vendor Breakdown:\n")
        for vendor, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_devices) * 100
            f.write(f"{vendor}: {count} devices ({percentage:.1f}%)\n")