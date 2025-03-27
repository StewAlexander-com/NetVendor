# NetVendor

## Introduction
*What vendors are lurking on your network? This software figures this out!*

NetVendor is a Python tool designed specifically for network administrators to analyze and visualize the vendor distribution of networking devices (routers and switches) in their infrastructure. It processes MAC address tables and IP ARP data from Cisco, HP/Aruba, and other network devices to provide detailed insights into your network's composition.

## Quick Navigation
- 🚀 [Getting Started](#getting-started) - Installation and setup
- 📋 [Features](#features) - What NetVendor can do
- 📖 [Usage Guide](#usage) - How to use the tool
- 📥 [Input/Output](#input) - File formats and results
- 📈 [Project Status](#project-status) - Updates and future plans

## Features
- Parses MAC address tables and ARP tables from Cisco routers and switches
- Identifies networking device vendors using MAC address OUI (Organizationally Unique Identifier) lookups
- Generates detailed reports and visualizations specifically tailored for network administrators
- Supports multiple input formats from common network devices:
  - Cisco IOS/IOS-XE show mac address-table
  - Cisco NX-OS show mac address-table
  - Cisco IOS/IOS-XE show ip arp
  - HP/Aruba show mac-address
  - Generic MAC address lists from other network devices
- Pre-seeded OUI database from Wireshark's manufacturers database
- Interactive HTML visualizations of vendor and VLAN distributions
- CSV exports for detailed device information

### Why Use NetVendor?
- **Network Security**: Network administrators can quickly identify unauthorized or unexpected devices on their network
- **Asset Management**: Track and manage network infrastructure by vendor
- **Network Visibility**: Clear visualization of device distribution across VLANs and ports
- **Port Analysis**: Detailed insights into port utilization and device connections on switches
- **Change Tracking**: Monitor network infrastructure changes over time
- **Efficiency**: Fast processing with progress tracking for large network datasets
- **Organization**: All output files are neatly organized for easy reference

### How It Works
1. **Device Discovery**
   - Uses pre-seeded Wireshark manufacturers database (53,000+ entries)
   - Multi-layered vendor lookup strategy:
     1. First tries pre-seeded cache (instant)
     2. Then checks user's local cache (fast)
     3. Finally attempts API lookup (if needed)
        - Rotates between multiple vendor lookup services
        - Implements rate limiting and exponential backoff
        - Caches successful lookups for future use
   - Shows real-time progress for each operation

2. **Data Organization**
   - Creates vendor-specific device lists in text format
   - Converts all results to CSV for spreadsheet analysis
   - Organizes files in a clean directory structure

3. **Visualization**
   - Interactive dashboard with multiple views:
     - Vendor distribution pie chart with detailed hover information
     - VLAN device count analysis
     - VLAN distribution per vendor heatmap
   - Easy navigation between different visualizations
   - Downloadable charts and data

4. **Analysis**
   - Identifies hidden VLANs
   - Maps devices to IP addresses
   - Tracks network composition changes
   - Provides plain text summaries for easy sharing

## Getting Started

### Prerequisites
- Working internet connection (for IEEE OUI database updates)
- Input file containing MAC addresses from network devices (routers and switches)
- Python 3.6 or higher
- Required Python packages:
  - requests
  - plotly
  - rich
  - tqdm

### Installation
1. Clone the repository:
```bash
git clone https://github.com/StewAlexander-com/NetVendor.git
cd NetVendor
```

2. Install the package:
```bash
pip install -e .
```

## Usage

### Basic Usage
Run the script with your network device output file:
```bash
netvendor input_file.txt
```

### Input File Format
The tool accepts output from common network device commands:

1. **Cisco IOS/IOS-XE MAC Address Table**
```
Vlan    Mac Address       Type        Ports
----    -----------      --------    -----
 10     0011.2233.4455   DYNAMIC     Gi1/0/1
```

2. **Cisco NX-OS MAC Address Table**
```
VLAN     MAC Address     Type        Port
----     -----------     --------    -----
 10      0011.2233.4455  dynamic     Eth1/1
```

3. **Cisco IOS/IOS-XE ARP Table**
```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.1            -   0011.2233.4455  ARPA   GigabitEthernet1/0/1
```

4. **HP/Aruba MAC Address Table**
```
MAC Address       Port    Type    VLAN
0011.2233.4455    1       dynamic 10
```

### Output Files
The tool generates several output files in the `output` directory:

1. **Device Information CSV**
   - Lists all discovered network devices
   - Includes MAC address, vendor, VLAN, and port information
   - Useful for inventory management and network documentation

2. **Port Report CSV** (for MAC address tables)
   - Shows port utilization on switches
   - Lists devices connected to each port
   - Includes VLAN and vendor information per port
   - Helps with network troubleshooting and capacity planning

3. **Vendor Distribution HTML**
   - Interactive dashboard with multiple visualizations
   - Vendor distribution pie chart
   - VLAN analysis charts
   - Device distribution across network segments
   - Helps network administrators understand their network composition

4. **Vendor Summary Text**
   - Plain text summary of vendor distribution
   - Quick reference for network documentation
   - Easy to share with team members

## Project Status
NetVendor is actively maintained and regularly updated with new features and improvements. Future plans include:
- Support for additional network device output formats
- Enhanced visualization options
- Network topology mapping
- Historical data tracking
- Integration with network management systems

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
