"""
Generate updated dashboard images for README.md

This script creates representative images of the ShadowVendor dashboard
with the latest styling improvements (v12.8+).
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# Create images directory if it doesn't exist
os.makedirs('images', exist_ok=True)

# Realistic sample data matching actual ShadowVendor output
vendors = [
    'Cisco Systems, Inc',
    'Hewlett Packard',
    'Dell Inc.',
    'Apple, Inc.',
    'Hewlett Packard Enterprise',
    'Juniper Networks'
]
devices = [95, 90, 88, 61, 54, 41]
total_devices = sum(devices)

# VLAN data for multi-panel visualization
vlans = ['VLAN 10', 'VLAN 20', 'VLAN 30', 'VLAN 40', 'VLAN 50', 'VLAN 60', 'VLAN 70']
vlan_devices = [12, 15, 8, 18, 22, 14, 16]
vlan_vendors = [4, 5, 3, 6, 5, 4, 5]

print("Generating updated dashboard images...")

# 1. Overview Image - Enhanced Pie Chart (matches actual dashboard)
fig_overview = go.Figure()
legend_labels = [f"{v} ({d})" for v, d in zip(vendors, devices)]
hover_text = [
    f"Vendor: {v}<br>Device Count: {d:,} devices<br>Percentage: {(d/total_devices)*100:.1f}%<br>Present in multiple VLANs"
    for v, d in zip(vendors, devices)
]

fig_overview.add_trace(
    go.Pie(
        labels=legend_labels,
        values=devices,
        hovertemplate="%{customdata}<br><extra></extra>",
        customdata=hover_text,
        textinfo='label',
        textposition='outside',
        hole=0.3
    )
)

fig_overview.update_layout(
    title={
        'text': 'Vendor Distribution',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20, 'color': '#2c3e50'}
    },
    showlegend=True,
    autosize=True,
    height=600,
    margin=dict(l=50, r=50, t=80, b=50),
    template='plotly_white',
    font=dict(family='Arial, sans-serif', size=12)
)

try:
    fig_overview.write_image('images/overview.png', width=1200, height=800, scale=2)
    print("✓ Generated overview.png")
except Exception as e:
    print(f"⚠ Could not generate overview.png: {e}")
    print("  (Install kaleido: pip install kaleido)")

# 2. Security Dashboard - VLAN Device Count (matches actual dashboard)
fig_security = go.Figure()
fig_security.add_trace(
    go.Bar(
        x=vlans,
        y=vlan_devices,
        name='Total Devices',
        hovertemplate="VLAN: %{x}<br>Devices: %{y}<extra></extra>",
        marker_color='rgb(55, 83, 109)'
    )
)

fig_security.update_layout(
    title={
        'text': 'Total Devices per VLAN',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18, 'color': '#2c3e50'}
    },
    xaxis_title='VLAN',
    yaxis_title='Number of Devices',
    width=1000,
    height=600,
    template='plotly_white',
    margin=dict(l=60, r=30, t=80, b=60),
    font=dict(family='Arial, sans-serif', size=12),
    xaxis=dict(tickangle=45)
)

try:
    fig_security.write_image('images/security-dashboard.png', width=1200, height=800, scale=2)
    print("✓ Generated security-dashboard.png")
except Exception as e:
    print(f"⚠ Could not generate security-dashboard.png: {e}")

# 3. Vendor Dashboard - Multi-panel VLAN Analysis (matches actual dashboard)
fig_vendor = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Total Devices per VLAN",
        "Unique Vendors per VLAN",
        "Vendor Distribution per VLAN",
        "Top Vendors per VLAN"
    ),
    vertical_spacing=0.15,
    horizontal_spacing=0.12
)

# Top row: Device count and unique vendors
fig_vendor.add_trace(
    go.Bar(
        x=vlans,
        y=vlan_devices,
        name='Total Devices',
        hovertemplate="VLAN: %{x}<br>Devices: %{y}<extra></extra>",
        marker_color='rgb(55, 83, 109)'
    ),
    row=1, col=1
)

fig_vendor.add_trace(
    go.Bar(
        x=vlans,
        y=vlan_vendors,
        name='Unique Vendors',
        hovertemplate="VLAN: %{x}<br>Vendors: %{y}<extra></extra>",
        marker_color='rgb(26, 118, 255)'
    ),
    row=1, col=2
)

# Bottom row: Heatmap and stacked bars
top_5_vendors = vendors[:5]
heatmap_data = [
    [3, 2, 1, 2, 1],  # VLAN 10
    [4, 3, 2, 3, 2],  # VLAN 20
    [2, 1, 1, 2, 1],  # VLAN 30
    [5, 4, 3, 3, 2],  # VLAN 40
    [6, 5, 4, 4, 2],  # VLAN 50
    [4, 3, 2, 3, 1],  # VLAN 60
    [5, 4, 3, 2, 1],  # VLAN 70
]

fig_vendor.add_trace(
    go.Heatmap(
        z=heatmap_data,
        x=top_5_vendors,
        y=vlans,
        colorscale='Viridis',
        showscale=True,
        hovertemplate="VLAN: %{y}<br>Vendor: %{x}<br>Devices: %{z}<extra></extra>"
    ),
    row=2, col=1
)

# Stacked bar chart for top 3 vendors
for i, vendor in enumerate(top_5_vendors[:3]):
    vendor_counts = [row[i] for row in heatmap_data]
    fig_vendor.add_trace(
        go.Bar(
            name=vendor,
            x=vlans,
            y=vendor_counts,
            hovertemplate="VLAN: %{x}<br>Vendor: " + vendor + "<br>Devices: %{y}<extra></extra>"
        ),
        row=2, col=2
    )

fig_vendor.update_layout(
    height=1000,
    showlegend=True,
    barmode='stack',
    margin=dict(l=50, r=50, t=100, b=50),
    template='plotly_white',
    font=dict(family='Arial, sans-serif', size=11)
)

# Update x-axis labels for better readability
for i in range(1, 5):
    fig_vendor.update_xaxes(tickangle=45, row=(i+1)//2, col=(i-1)%2+1)

try:
    fig_vendor.write_image('images/vendor-dashboard.png', width=1400, height=1200, scale=2)
    print("✓ Generated vendor-dashboard.png")
except Exception as e:
    print(f"⚠ Could not generate vendor-dashboard.png: {e}")

print("\nImage generation complete!")
print("Note: If images were not generated, install kaleido: pip install kaleido") 