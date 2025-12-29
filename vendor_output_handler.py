"""
Output Handler for ShadowVendor

This module handles all output generation functionality including:
- CSV file creation
- Port report generation
- Vendor distribution visualization
- Text summary creation
"""

import csv
from pathlib import Path
from typing import Dict, List, Counter
from collections import Counter, defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

def make_csv(input_file: Path, devices: Dict[str, Dict[str, str]], oui_manager) -> None:
    """Creates a CSV file with device information."""
    output_file = Path("output") / f"{input_file.stem}-Devices.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vlan = info.get('vlan', 'N/A')
            port = info.get('port', 'N/A')
            writer.writerow([mac, vendor, vlan, port])
    
    console.print(f"\nDevice information written to {output_file}")

def generate_port_report(input_file: Path, devices: Dict[str, Dict[str, str]], oui_manager, is_mac_address_table) -> None:
    """Creates a CSV report with port-based device information."""
    # Only generate port report for MAC address tables
    if not is_mac_address_table:
        return

    # Initialize port data structure
    ports = {}
    
    # Process each device and organize by port
    for mac, info in devices.items():
        port = info.get('port')
        if not port:
            continue
            
        vlan = info.get('vlan', 'Unknown')
        vendor = oui_manager.get_vendor(mac)
        
        if port not in ports:
            ports[port] = {
                'devices': [],
                'vlan_count': Counter(),
                'vendor_count': Counter()
            }
            
        ports[port]['devices'].append((mac, vendor, vlan))
        ports[port]['vlan_count'][vlan] += 1
        ports[port]['vendor_count'][vendor] += 1
    
    # Create output file
    output_file = input_file.stem + '-Ports.csv'
    output_path = Path('output') / output_file
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Port', 'Total Devices', 'VLANs', 'Vendors', 'Device Details'])
        
        # Sort ports for consistent output
        for port_name in sorted(ports.keys()):
            port_info = ports[port_name]
            
            # Sort VLANs and vendors for readability
            vlans = sorted(port_info['vlan_count'].keys())
            vendors = sorted(port_info['vendor_count'].keys())
            
            # Create detailed device list
            device_details = []
            for mac, vendor, vlan in sorted(port_info['devices']):
                device_details.append(f"{mac} ({vendor}, VLAN {vlan})")
            
            writer.writerow([
                port_name,
                len(port_info['devices']),
                ','.join(vlans),
                ','.join(vendors),
                ' / '.join(device_details)
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
        # Process device data
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
        
        # Create and save the HTML visualization
        _create_html_visualization(
            vendor_counts,
            vlan_vendor_data,
            vendor_vlan_data,
            vlan_total_devices,
            vlan_unique_vendors,
            progress
        )

def save_vendor_summary(devices: Dict[str, Dict[str, str]], oui_manager, input_file: Path) -> None:
    """Create a plain text summary of vendor distribution."""
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
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(separator)
        f.write(column_header)
        f.write(separator.replace('-', '='))  # Double separator under headers
        for row in rows:
            f.write(row)
        f.write(separator)
    
    console.print(f"\nVendor summary written to {output_file}")

def _create_html_visualization(
    vendor_counts: Counter,
    vlan_vendor_data: defaultdict,
    vendor_vlan_data: defaultdict,
    vlan_total_devices: Counter,
    vlan_unique_vendors: Counter,
    progress: Progress
) -> None:
    """Helper function to create the HTML visualization."""
    # Create vendor distribution chart
    chart1_task = progress.add_task("[cyan]Creating vendor distribution chart...", total=100)
    
    # Create pie chart for overall vendor distribution
    fig1 = go.Figure()
    sorted_vendors = sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [v[0] for v in sorted_vendors]
    values = [v[1] for v in sorted_vendors]
    total_devices = sum(vendor_counts.values())
    
    # Create hover text and legend labels
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
    
    # Add pie chart trace
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
    
    # Update layout
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
    
    # Create VLAN analysis charts
    chart2_task = progress.add_task("[cyan]Creating VLAN analysis charts...", total=100)
    
    # Create subplot figure
    fig2 = _create_vlan_analysis_subplots(
        sorted_vendors,
        vlan_vendor_data,
        vendor_vlan_data,
        vlan_total_devices,
        vlan_unique_vendors,
        progress,
        chart2_task
    )
    
    # Save visualizations
    save_task = progress.add_task("[cyan]Saving visualizations...", total=100)
    _save_html_output(fig1, fig2, progress, save_task)

def _create_vlan_analysis_subplots(
    sorted_vendors,
    vlan_vendor_data,
    vendor_vlan_data,
    vlan_total_devices,
    vlan_unique_vendors,
    progress,
    chart2_task
) -> go.Figure:
    """Helper function to create VLAN analysis subplots."""
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
    
    # Add traces for each subplot
    _add_vlan_traces(
        fig2,
        sorted_vlans,
        sorted_vendors,
        vlan_vendor_data,
        vendor_vlan_data,
        vlan_total_devices,
        vlan_unique_vendors
    )
    
    # Update layout
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
    
    # Update axes
    for i in range(1, 5):
        fig2.update_xaxes(tickangle=45, row=(i+1)//2, col=(i-1)%2+1)
    
    progress.update(chart2_task, completed=100)
    return fig2

def _add_vlan_traces(
    fig2,
    sorted_vlans,
    sorted_vendors,
    vlan_vendor_data,
    vendor_vlan_data,
    vlan_total_devices,
    vlan_unique_vendors
):
    """Helper function to add traces to the VLAN analysis subplots."""
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
    
    # 2. Unique Vendors per VLAN
    fig2.add_trace(
        go.Bar(
            x=[f"VLAN {v}" for v in sorted_vlans],
            y=[vlan_unique_vendors[vlan] for vlan in sorted_vlans],
            name="Unique Vendors",
            hovertemplate="VLAN: %{x}<br>Unique Vendors: %{y}<extra></extra>",
            marker_color='rgb(26, 118, 255)'
        ),
        row=1, col=2
    )
    
    # 3. Vendor Distribution Heatmap
    top_vendors = [v[0] for v in sorted_vendors[:20]]
    heatmap_data = [
        [vendor_vlan_data[vendor][vlan] for vlan in sorted_vlans]
        for vendor in top_vendors
    ]
    
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
    
    # 4. Top Vendors per VLAN Stacked Bar Chart
    top_5_vendors = [v[0] for v in sorted_vendors[:5]]
    for vendor in top_5_vendors:
        vendor_counts = [vendor_vlan_data[vendor][vlan] for vlan in sorted_vlans]
        fig2.add_trace(
            go.Bar(
                name=vendor,
                x=[f"VLAN {v}" for v in sorted_vlans],
                y=vendor_counts,
                hovertemplate="VLAN: %{x}<br>Vendor: " + vendor + "<br>Devices: %{y}<extra></extra>"
            ),
            row=2, col=2
        )

def _save_html_output(fig1, fig2, progress, save_task):
    """Helper function to save the HTML visualization output."""
    output_file = Path("output") / "vendor_distribution.html"
    with open(output_file, 'w') as f:
        # Write HTML header and styling
        f.write(_get_html_header())
        
        progress.update(save_task, completed=40)
        f.write(fig1.to_html(full_html=False, include_plotlyjs=True))
        
        progress.update(save_task, completed=70)
        f.write(_get_html_middle())
        f.write(fig2.to_html(full_html=False, include_plotlyjs=False))
        f.write('</div></div></body></html>')
        
        progress.update(save_task, completed=100)
        
    console.print(f"\nVisualizations written to {output_file}")

def _get_html_header():
    """Returns the HTML header with styling."""
    return """
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
                document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
                document.querySelectorAll('.page-nav a').forEach(link => link.classList.remove('active'));
                document.getElementById('page' + pageNum).classList.add('active');
                document.querySelector('.page-nav a[data-page="' + pageNum + '"]').classList.add('active');
                window.dispatchEvent(new Event('resize'));
            }
            
            window.onload = () => {
                showPage(1);
                function updateChartSizes() {
                    const containers = document.querySelectorAll('.chart-container');
                    containers.forEach(container => {
                        const viewportWidth = window.innerWidth;
                        const viewportHeight = window.innerHeight;
                        const charts = container.getElementsByClassName('plotly-graph-div');
                        Array.from(charts).forEach(chart => {
                            const hasSubplots = chart.layout && chart.layout.grid && chart.layout.grid.rows > 1;
                            let width = hasSubplots ? Math.min(viewportWidth * 0.9, 1800) : Math.min(viewportWidth * 0.85, 1600);
                            let height = hasSubplots ? Math.min(viewportHeight * 1.2, 1200) : Math.min(viewportHeight * 0.8, 900);
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
    """

def _get_html_middle():
    """Returns the HTML middle section."""
    return """
            </div>
        </div>
        <div id="page2" class="page">
            <div class="description">
                Comprehensive VLAN analysis showing device distribution, vendor diversity,
                and relationships between VLANs and vendors. Use the interactive features
                to explore specific VLANs and vendors.
            </div>
            <div class="chart-container">
    """ 