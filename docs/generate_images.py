import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os

# Create images directory if it doesn't exist
os.makedirs('images', exist_ok=True)

# Sample data for demonstration
vendors = ['Cisco', 'HP', 'Dell', 'Apple', 'Samsung', 'Other']
devices = [300, 250, 200, 150, 100, 50]
vlan_data = {
    'VLAN': ['VLAN 10', 'VLAN 20', 'VLAN 30', 'VLAN 40', 'VLAN 50'],
    'Devices': [150, 200, 100, 250, 300],
    'Vendors': [3, 4, 2, 5, 4]
}

# 1. Overview Image (Pie Chart)
fig_overview = go.Figure(data=[go.Pie(labels=vendors, values=devices)])
fig_overview.update_layout(
    title='Network Device Vendor Distribution',
    showlegend=True,
    width=800,
    height=600,
    template='plotly_white'
)
fig_overview.write_image('images/overview.png')

# 2. Security Dashboard (Bar Chart with Security Indicators)
fig_security = go.Figure()
fig_security.add_trace(go.Bar(
    x=vendors,
    y=devices,
    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
))
fig_security.update_layout(
    title='Device Distribution by Vendor',
    xaxis_title='Vendor',
    yaxis_title='Number of Devices',
    width=800,
    height=600,
    template='plotly_white'
)
fig_security.write_image('images/security-dashboard.png')

# 3. Vendor Distribution Dashboard (Multi-panel)
fig_vendor = go.Figure()
fig_vendor.add_trace(go.Bar(
    x=vlan_data['VLAN'],
    y=vlan_data['Devices'],
    name='Devices per VLAN'
))
fig_vendor.add_trace(go.Bar(
    x=vlan_data['VLAN'],
    y=vlan_data['Vendors'],
    name='Vendors per VLAN'
))
fig_vendor.update_layout(
    title='VLAN Analysis',
    xaxis_title='VLAN',
    yaxis_title='Count',
    barmode='group',
    width=800,
    height=600,
    template='plotly_white'
)
fig_vendor.write_image('images/vendor-dashboard.png') 