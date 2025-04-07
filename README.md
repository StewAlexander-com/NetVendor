# NetVendor

## Introduction
NetVendor is a Python-based network analysis tool designed to help network administrators and security professionals identify and analyze network devices by their MAC addresses. It processes MAC address tables and ARP data from network devices, providing detailed vendor information and network composition analysis.

## Features
- Processes MAC addresses from various input formats:
  * Simple MAC address lists
  * Switch MAC address tables
  * ARP tables
- Identifies device vendors using IEEE OUI database
- Generates detailed reports and visualizations
- Supports multiple network device output formats
- Provides VLAN and port analysis
- Creates interactive HTML dashboards
- Maintains a local OUI cache for fast lookups

## Installation

### Prerequisites
- Python 3.6 or higher
- Required packages:
  * requests
  * plotly
  * rich
  * tqdm

### Setup
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

### Basic Command
```bash
netvendor input_file.txt
```

### Windows Usage
For Windows systems, run from PowerShell:
```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
python3 -m netvendor input_file.txt
```

## Input File Format
The tool supports three main types of input files:

1. **Simple MAC Address List**
```
00:11:22:33:44:55
00:AA:BB:CC:DD:EE
40:B0:76:12:34:56
```

2. **MAC Address Tables** (Cisco/HP/Aruba format)
```
Vlan    Mac Address       Type        Ports
----    -----------      --------    -----
 10     0011.2233.4455   DYNAMIC     Gi1/0/1
 20     00aa.bbcc.ddee   DYNAMIC     Gi1/0/2
```

3. **ARP Tables**
```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.1            -   0011.2233.4455  ARPA   Vlan10
Internet  192.168.1.2           10   00aa.bbcc.ddee  ARPA   Vlan20
```

### Enhanced Format Detection
- Automatic file type identification
- Support for multiple MAC address formats:
  * Colon-separated (00:11:22:33:44:55)
  * Dot-separated (0011.2233.4455)
  * No separators (001122334455)
- Intelligent VLAN extraction:
  * From MAC table VLAN column
  * From ARP table interface field
  * Defaults to "N/A" for simple lists
- Automatic header detection and skipping
- Port information preservation where available

## Output Files
The tool generates several files in the `output` directory:

1. **Device Information CSV**
- Complete device inventory
- MAC addresses with vendor information
- VLAN and port details
- Last seen timestamps

2. **Vendor Distribution HTML**
- Interactive charts
- Network composition visualization
- VLAN distribution analysis
- Device type breakdown

3. **Vendor Summary Text**
- Quick reference summary
- Total device counts by vendor
- VLAN statistics
- Port utilization overview

## Project Status
NetVendor is actively maintained with regular updates:

### Recent Improvements
- Enhanced file format detection
- Improved VLAN extraction
- Better MAC address format handling
- Automatic header detection
- Cleaner output presentation

### Upcoming Features
- Additional device format support
- Enhanced visualization options
- Network topology mapping
- Historical data tracking
- Management system integration

## Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues for improvements.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Author
Stewart Alexander

## Acknowledgments
- IEEE for OUI database access
- Open source community for various Python packages