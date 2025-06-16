# NetVendor

## Introduction

**NetVendor** is a Python tool for network administrators and cybersecurity professionals to analyze and visualize the vendor distribution of devices on a network. It processes MAC address tables and ARP data from a wide range of network devices (including Cisco, HP/Aruba, Juniper, Extreme, Brocade, and more), providing detailed insights into your network's composition.

---

## Features

- **Multi-vendor MAC address parsing:** Supports Cisco, HP/Aruba, Juniper, Extreme, Brocade, and more.
- **Flexible input:** Accepts MAC address lists, MAC tables, and ARP tables in various formats.
- **Vendor identification:** Uses a local IEEE OUI cache for fast, secure lookups.
- **Comprehensive reporting:** Generates CSVs, summaries, and interactive HTML dashboards.
- **VLAN and port analysis:** Extracts and visualizes VLAN and port data where available.
- **Extensible and robust:** Easily add support for new formats; thoroughly tested with real-world data.

---

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Required packages: `requests`, `plotly`, `rich`, `tqdm`
- Input file containing MAC addresses or ARP data from your network devices

### Installation

```bash
git clone https://github.com/StewAlexander-com/NetVendor.git
cd NetVendor
pip install -e .
```

---

## Usage

### Basic Command

```bash
netvendor input_file.txt
```

### Windows Usage

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
python3 -m netvendor input_file.txt
```

---

## Supported Input Formats

NetVendor automatically detects and parses the following formats:

### 1. Simple MAC Address List

```
00:11:22:33:44:55
00-11-22-33-44-55
001122334455
0011.2233.4455
```

### 2. MAC Address Tables (Multi-vendor)

```
Vlan    Mac Address       Type        Ports
10      0011.2233.4455    DYNAMIC     Gi1/0/1
20      00:0E:83:11:22:33 DYNAMIC     ge-0/0/0
30      B8:AC:6F:77:88:99 DYNAMIC     1:1
```

- **Cisco:** `0011.2233.4455`, `Gi1/0/1`
- **HP/Aruba:** `00:24:81:44:55:66`, `1`
- **Juniper:** `00:0E:83:11:22:33/ff:ff:ff:ff:ff:ff`, `ge-0/0/0`
- **Extreme:** `B8-AC-6F-77-88-99/ff-ff-ff-ff-ff-ff`, `1:1`
- **Brocade:** `00:11:22:33:44:55/ffff.ffff.ffff`, `1/1`

### 3. ARP Tables

```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.1      -          0011.2233.4455  ARPA   Vlan10
```

---

## Enhanced Format Detection

- **Automatic file type detection** based on content
- **Flexible MAC parsing:** Accepts colon, hyphen, dot, and mask/prefix formats
- **VLAN extraction** from multiple sources (column, interface, etc.)
- **Port extraction** for detailed switch analysis
- **Header skipping** and robust error handling

---

## Output

All results are saved in the `output` directory:

- **Device Information CSV:** MAC, Vendor, VLAN, Port
- **Port Report CSV:** Port utilization and device mapping
- **Vendor Distribution HTML:** Interactive dashboard with charts
- **Vendor Summary Text:** Quick reference for documentation

---

## Project Status

NetVendor is actively maintained and regularly updated.  
**Recent improvements:**
- Enhanced MAC address parsing for Juniper, Aruba, Extreme, Brocade, and more
- Improved OUIManager logic and normalization
- Real-world OUI test coverage
- All tests pass and program output confirmed

**Planned:**
- More vendor format support
- Additional visualization options
- Network topology mapping
- Historical data tracking

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

MIT License

## Author

Stewart Alexander

---

**Tip:** For best results, always use the latest OUI cache and keep your dependencies up to date.
