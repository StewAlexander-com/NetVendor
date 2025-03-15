# NetVendor

## Contents
- [NetVendor](#netvendor)
  - [Contents](#contents)
  - [Overview](#overview)
    - [Why Use NetVendor?](#why-use-netvendor)
    - [How It Works](#how-it-works)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Dependencies](#dependencies)
  - [Usage](#usage)
    - [Input](#input)
    - [Output](#output)
  - [Features](#features)
    - [File Structure](#file-structure)
  - [Project Status](#project-status)
    - [Updates and Changes](#updates-and-changes)
    - [Future Enhancements](#future-enhancements)
  - [About](#about)
    - [Author](#author)

---

[Rest of the file remains unchanged...]

---

A Python tool for analyzing network device vendors from MAC address tables or IP ARP data. NetVendor helps network administrators identify and track devices on their network by vendor, providing organized output and visual analytics.

*What vendors are lurking on your network? This software figures this out!*

**Quick Navigation:**
- 🚀 [Installation](#installation) - Get started in minutes
- 📋 [Features](#features) - What NetVendor can do
- 📖 [Usage Guide](#usage) - How to use the tool
- 📥 [Input/Output](#input) - File formats and results
- 📈 [Latest Updates](#updates-and-changes) - Recent improvements
- 🔮 [Future Plans](#future-enhancements) - What's coming next

## Overview

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

### Installation
```bash
# Clone the repository
git clone https://github.com/StewAlexander-com/NetVendor.git
cd NetVendor

# Install dependencies
pip install -r requirements.txt

# Run the program
python NetVendor.py
```

### Dependencies 
Required for operation:
- Working internet connection (for IEEE OUI database updates)
- Input file containing MAC addresses
- Python 3.6 or higher
- Required Python packages (installed via `pip install -r requirements.txt`)

## Usage
Run the script:
```bash
python NetVendor.py
```

The script will:
1. Check for required dependencies
2. Update the OUI database if needed (downloads from IEEE)
3. Prompt for input file and column information
4. Process devices and generate reports with progress visualization
5. Create pie charts and CSV files
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
The program generates an organized structure of output files under the `output/` directory:

1. **Vendor Device Files** (`output/text_files/`)
   - Individual text files for Apple, Cisco, Dell, HP, and Mitel devices
   - Original data format preserved

2. **CSV Files** (`output/csv_files/`)
   - Spreadsheet-ready versions of all device files
   - Easy to import into Excel or other tools

3. **Visualization** (`output/plots/`)
   - Pie chart showing vendor distribution
   - Percentage breakdown of all vendors
   - "Other" category for unidentified devices

4. **OUI Database** (`output/data/`)
   - Cached IEEE OUI database
   - Vendor mappings and timestamps
   - Regular updates from IEEE

## Features
- Identifies devices from major vendors (Apple, Cisco, Dell, HP, Mitel)
- Creates vendor-specific device lists with progress tracking
- Generates pie charts of vendor distribution
- Converts results to CSV format
- Maintains an up-to-date OUI database from IEEE
- Rich progress visualization for all operations
- Organized output file structure

### File Structure
```
NetVendor/
├── NetVendor.py          # Main application
├── oui_manager.py        # OUI database manager
├── requirements.txt      # Python dependencies
└── output/              # Generated at runtime
    ├── data/            # OUI database storage
    ├── text_files/      # Vendor device text files
    ├── csv_files/       # Converted CSV files
    └── plots/           # Generated charts
```

## Project Status

### Updates and Changes
Latest updates (March 15, 2024):
- Added OUI manager for dynamic vendor identification
- Improved progress visualization with rich library
- Consolidated output files under organized directory structure
- Added proper .gitignore for sensitive data protection
- Added requirements.txt for dependency management
- Removed browser dependency for pie charts
- Improved documentation and code organization

For previous updates, see our [Updates History](#updates-and-changes).

### Future Enhancements
High Priority:
- Add more vendor checks and OUI patterns
- Add command line arguments for automation
- Add error handling for network connectivity issues
- Add logging for troubleshooting

Medium Priority:
- Add configuration file for customizable settings
- Add unit tests and integration tests
- Add historical data comparison
- Add export to additional formats

Low Priority:
- Add web interface for easier use
- Add network scanning capabilities
- Add detailed vendor statistics
- Add report generation

## About

### Author
Created by Stew Alexander (2021)
