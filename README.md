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
- Identifies devices from major vendors (Apple, Cisco, Dell, HP, Mitel)
- Creates vendor-specific device lists with progress tracking
- Generates interactive visualizations:
  - Vendor distribution pie chart with hover details
  - VLAN device count analysis
  - VLAN distribution per vendor heatmap
  - Port-based device analysis (for MAC address tables)
- Converts results to CSV format
- Maintains an up-to-date OUI database from IEEE
- Rich progress visualization for all operations
- Organized output file structure
- Plain text summaries for easy sharing

### Why Use NetVendor?
- **Security**: Understanding what exists in your network is essential for security
- **Asset Management**: Easy identification of vendor devices
- **Network Visibility**: Clear visualization of device distribution
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
```bash
# Clone the repository
git clone https://github.com/StewAlexander-com/NetVendor.git
cd NetVendor

# Install dependencies
pip install -r requirements.txt
```

## Usage
Run the script:
```bash
python NetVendor.py <input_file>
```

The script will:
1. Check for required dependencies
2. Process devices with progress visualization
3. Generate an interactive dashboard with multiple visualizations
4. Create a plain text summary and CSV report
5. Organize all output files in the `output` directory

### Input
The program accepts ARP or MAC address tables as input, such as:
- Cisco IOS `show ip arp`
- Cisco IOS `show mac address-table`
- Any text file containing MAC addresses in a column

Example input format:
```
Internet  10.0.0.1   1   0123.4567.89ab  ARPA   Vlan100
Internet  10.0.0.2   1   abcd.ef01.2345  ARPA   Vlan100
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

<img src="https://github.com/user-attachments/assets/42877728-d2df-4ef4-a9db-b5c80a008be2" 
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
     - Port identifier
     - Total devices per port
     - VLANs present on each port
     - Vendors present on each port
     - Detailed device information per port

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

### Latest Updates (March 2024)
- Added port-based analysis for MAC address tables:
  - Detailed port-to-device mapping
  - VLAN distribution per port
  - Vendor distribution per port
  - Comprehensive device details per port
- Enhanced performance and reliability:
  - Smarter rate limiting with 250ms intervals and retry logic
  - Efficient cache management (saves every 50 entries)
  - Optimized memory usage with batch processing
  - Improved progress tracking with separate progress bars
- Improved visualization dashboard:
  - Responsive design that adapts to window size
  - Enhanced pie chart with better spacing and readability
  - Improved VLAN analysis graphs with proper spacing
  - Better navigation between visualization pages
  - Centered layout with optimized dimensions
  - Enhanced vendor list formatting
- Added interactive dashboard with multiple visualizations
- Implemented VLAN analysis with device count tracking
- Added VLAN distribution per vendor heatmap
- Created plain text summary output
- Enhanced pie chart with detailed hover information
- Improved legend formatting and positioning
- Enhanced documentation and usage instructions

### Future Enhancements
**High Priority:**
- Add more vendor checks and OUI patterns
- Add command line arguments for automation
- Add error handling for network connectivity issues
- Add logging for troubleshooting

**Medium Priority:**
- Add configuration file for customizable settings
- Add unit tests and integration tests
- Add historical data comparison
- Add export to additional formats

**Low Priority:**
- Add web interface for easier use
- Add network scanning capabilities
- Add detailed vendor statistics
- Add report generation

### Author
Created by Stew Alexander (2021)
