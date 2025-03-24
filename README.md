# NetVendor

## Introduction
*What vendors are lurking on your network? This software figures this out!*

NetVendor is a Python tool for analyzing network device vendors from MAC address tables or IP ARP data. It helps network administrators identify and track devices on their network by vendor, providing organized output and visual analytics.

## Quick Navigation
- 🚀 [Getting Started](#getting-started) - Installation and setup
- 📋 [Features](#features) - What NetVendor can do
- 📖 [Usage Guide](#usage) - How to use the tool
- 📥 [Input/Output](#input) - File formats and results
- 📈 [Project Status](#project-status) - Updates and future plans

## Features
- Parses MAC address tables and ARP tables from various network devices
- Identifies device vendors using MAC address OUI (Organizationally Unique Identifier) lookups
- Generates detailed reports and visualizations
- Supports multiple input formats:
  - Cisco IOS/IOS-XE show mac address-table
  - Cisco NX-OS show mac address-table
  - Cisco IOS/IOS-XE show ip arp
  - HP/Aruba show mac-address
  - Generic MAC address lists
- Pre-seeded OUI database from Wireshark's manufacturers database
- Interactive HTML visualizations of vendor and VLAN distributions
- CSV exports for detailed device information

### Why Use NetVendor?
- **Security**: Understanding what exists in your network is essential for security
- **Asset Management**: Easy identification of vendor devices
- **Network Visibility**: Clear visualization of device distribution
- **Port Analysis**: Detailed insights into port utilization and device connections
- **Change Tracking**: Benchmark your network to easily see changes
- **Efficiency**: Fast processing with progress tracking
- **Organization**: All output files are neatly organized

### How It Works
1. **Device Discovery**
   - Downloads the latest IEEE OUI database
   - Identifies devices from major vendors (Apple, Cisco, Dell, HP, Mitel)
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
- Input file containing MAC addresses
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
Run the script:
```bash
netvendor input_file.txt
```

The script will:
1. Check for required dependencies
2. Process devices with progress visualization
3. Generate an interactive dashboard with multiple visualizations
4. Create a plain text summary and CSV report
5. Organize all output files in the `output` directory

### Updating the OUI Cache

The package includes a pre-seeded `oui_cache.json` file containing manufacturer information from Wireshark's database. This cache is automatically installed with the package and used by default. However, if you need to update the cache with the latest manufacturer information, you can run:

```bash
update-oui-cache
```

This will fetch the latest manufacturer database from Wireshark and update your local cache.

### Input File Formats
The tool supports several input file formats:

1. Cisco IOS/IOS-XE show mac address-table:
```
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
 100    0001.0001.0001    DYNAMIC     Gi1/0/1
```

2. Cisco NX-OS show mac address-table:
```
* - primary entry, G - Gateway MAC, (R) - Routed MAC, O - Overlay MAC
age - seconds since last seen,+ - primary entry using vPC Peer-Link, (T) - True, (E) - Egress
   VLAN     MAC Address     Type      age     Secure NTFY Ports/SWID.SSID.LID
---------+-----------------+--------+---------+------+----+------------------
* 100     0001.0001.0001   dynamic  0         F     F  Eth1/1
```

3. Cisco IOS/IOS-XE show ip arp:
```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.1            -   0001.0001.0001  ARPA   GigabitEthernet1/0/1
```

4. HP/Aruba show mac-address:
```
MAC Address         VLAN    Type    Port
----------------    ----    ----    ----
0001-0001-0001      100     DYNAMIC 1
```

5. Generic MAC address list:
```
0001.0001.0001
0002.0002.0002
```

### Output
NetVendor generates five types of output:

1. **Console Output**
   - Real-time dependency checks
   - Progress bars for MAC address processing
   - Summary table showing vendor distribution

2. **Interactive HTML Dashboard** (`output/vendor_distribution.html`)

<img src="https://github.com/user-attachments/assets/f6bd4671-81c2-4317-9344-08e6dd65d9ec" 
     alt="Screenshot 2025-03-18 at 3 29 24 PM" 
     style="width: 67%; height: auto">
---     

<img src="https://github.com/user-attachments/assets/b967ed89-b976-4c70-88f2-88145ce427b6" 
     alt="Screenshot 2025-03-18 at 3 30 59 PM" 
     style="width: 67%; height: auto">
 
   - Page 1: Vendor Distribution
     - Large, centered interactive pie chart showing vendor distribution
     - Comprehensive hover information for each vendor:
       - Total device count with thousands separators
       - Percentage of network devices
       - Number of VLANs the vendor appears in
       - Most commonly used VLAN
       - Maximum devices in any single VLAN
     - Detailed vendor list with device counts
     - Clean, modern layout with optimized spacing
   - Page 2: VLAN Analysis
     - Four well-spaced analysis graphs:
       - Top VLANs by total device count
       - Vendor presence across VLANs
       - VLAN distribution patterns
       - Device concentration heatmap
     - Interactive tooltips and zoom capabilities
     - Responsive layout that adapts to window size
     - Clear visualization of VLAN relationships

   Features:
   - Easy navigation between pages via fixed top-right menu
   - Responsive design that adjusts to browser window size
   - Optimized spacing and centering for better readability
   - Professional styling with consistent fonts and colors
   - Interactive elements for detailed data exploration

4. **Plain Text Summary** (`output/vendor_summary.txt`)
   - Clean, ASCII-formatted table
   - Vendor names, device counts, and percentages
   - Easy to share in emails or documents

5. **CSV Report** (`output/[input-filename]-Devices.csv`)
   - Detailed device information including:
     - IP Address
     - MAC Address
     - VLAN
     - Vendor

6. **Port Analysis Report** (`output/[input-filename]-Ports.csv`) - *For MAC address tables only*
   - Comprehensive port-based analysis including:
     - Port identifier (e.g., Gi1/0/1, Fa1/0/1)
     - Total connected devices per port
     - List of VLANs present on each port
     - List of vendors present on each port
     - Detailed device information including:
       - MAC addresses with vendor names
       - VLAN assignments per device
       - Port-to-device mapping for network topology
     - Useful for:
       - Identifying heavily utilized ports
       - Detecting unauthorized devices or VLANs
       - Planning network segmentation
       - Troubleshooting connectivity issues
       - Auditing network access and security

### Output Directory Structure
```
NetVendor/
├── NetVendor.py          # Main application
├── oui_cache.json        # Cached vendor lookups
└── output/               # Generated at runtime
    ├── vendor_distribution.html    # Interactive dashboard
    ├── vendor_summary.txt          # Plain text summary
    ├── [input-filename]-Devices.csv  # Detailed device list
    └── [input-filename]-Ports.csv    # Port analysis (MAC tables only)
```

## Project Status

### Latest Updates (March 2025)
- Refactored codebase for better maintainability [72fa9f4]:
  - Modularized output handling into separate module
  - Added comprehensive unit tests
  - Improved code organization and documentation
- Enhanced OUI cache management [31e53ed]:
  - Pre-seeded OUI cache from Wireshark's database
  - Added standalone update-oui-cache utility
  - Improved cache update reliability using system curl
- Improved port analysis capabilities [1c4de02]:
  - Detailed port-to-device mapping
  - VLAN distribution per port
  - Vendor distribution per port
  - Comprehensive device details per port
- Enhanced visualization dashboard:
  - Interactive vendor distribution pie charts
  - VLAN analysis graphs with proper spacing
  - Better navigation between visualization pages
  - Centered layout with optimized dimensions
  - Enhanced vendor list formatting
  - Detailed hover information for all charts

### Future Enhancements
**High Priority:**
- Add support for more network device output formats
- Implement configuration file for customizable settings
- Add command line arguments for automation
- Expand test coverage

**Medium Priority:**
- Add historical data comparison
- Support for bulk file processing
- Add network scanning capabilities
- Add export to additional formats

**Low Priority:**
- Create web interface for easier use
- Add detailed vendor statistics
- Add custom report templates
- Support for real-time monitoring

### Author
Created by Stew Alexander (2021)

## Dependencies

- Python 3.8 or higher
- requests
- plotly
- tqdm
- rich
- curl (system command for OUI cache updates)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
