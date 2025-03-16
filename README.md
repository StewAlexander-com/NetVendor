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
- Generates pie charts of vendor distribution
- Converts results to CSV format
- Maintains an up-to-date OUI database from IEEE
- Rich progress visualization for all operations
- Organized output file structure

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
   - Generates pie charts showing vendor distribution
   - Provides detailed device counts
   - Shows percentage breakdowns

4. **Analysis**
   - Identifies hidden VLANs
   - Maps devices to IP addresses
   - Tracks network composition changes

## Getting Started

### Prerequisites
- Working internet connection (for IEEE OUI database updates)
- Input file containing MAC addresses
- Python 3.6 or higher

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
python NetVendor.py
```

The script will:
1. Check for required dependencies
2. Update the OUI database if needed (downloads from IEEE)
3. Prompt for Mac Address input file and column information
4. Process devices and generate reports with progress visualization
5. Create pie charts and CSV files (for spreadsheets like Excel / Google Sheets etc)
6. Organize all output files in the `output` directory

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
NetVendor generates three types of output:

1. **Console Output**
   - Real-time dependency checks
   - Progress bars for MAC address processing
   - Summary table showing vendor distribution with:
     - Vendor names
     - Device counts
     - Percentage of total devices

2. **Interactive HTML Visualization** (`output/vendor_distribution.html`)
   - Interactive pie chart showing vendor distribution
   - Hover tooltips with detailed information
   - Legend for easy vendor identification
   - Ability to show/hide vendors
   - Download chart as PNG option

3. **CSV Report** (`output/[input-filename]-Devices.csv`)
   - Detailed device information in spreadsheet format
   - Columns include:
     - IP Address
     - MAC Address
     - VLAN
     - Vendor

### Output Directory Structure
```
NetVendor/
├── NetVendor.py          # Main application
├── oui_cache.json        # Cached vendor lookups
└── output/              # Generated at runtime
    ├── vendor_distribution.html    # Interactive pie chart
    └── [input-filename]-Devices.csv  # Detailed device list
```

## Project Status

### Latest Updates (March 15, 2024)
- Added OUI manager for dynamic vendor identification
- Improved progress visualization with rich library
- Consolidated output files under organized directory structure
- Added proper .gitignore for sensitive data protection
- Added requirements.txt for dependency management
- Removed browser dependency for pie charts
- Improved documentation and code organization

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
