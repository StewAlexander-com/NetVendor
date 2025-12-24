# 🚀 NetVendor

![Overview](docs/images/overview.png?v=12.8)
*Interactive vendor distribution pie chart with detailed hover information - see device counts, percentages, and VLAN presence at a glance*

## ⚡ TL;DR: Why You Should Care

- **Turn MAC tables into dashboards**: Transform raw network device outputs into interactive HTML visualizations and CSV reports
- **Detect new/unknown vendors**: Identify previously unseen devices and track vendor distribution changes over time
- **Export SIEM events**: Generate normalized CSV/JSONL exports for Elastic, Splunk, and other SIEMs to enable posture-change detection

**Quick start:** `python3 NetVendor.py input_file.txt` → Check `output/` for results

**Try it in 60 seconds:** `python3 NetVendor.py tests/data/test-mac-table.txt` (then open `output/vendor_distribution.html` in your browser) → See dashboards without touching your own network data

## 👥 Who is This For?

- **SOC analysts**: Detect new vendors and track device changes for security monitoring
- **Network engineers**: Analyze MAC address tables and ARP data to understand network composition
- **Asset/CMDB owners**: Maintain accurate device inventories with vendor identification
- **Security architects**: Integrate posture-change detection into SIEM workflows

---

## 📖 Introduction

**NetVendor** is a Python tool for network administrators and cybersecurity professionals to analyze and visualize the vendor distribution of devices on a network. It processes MAC address tables and ARP data from a wide range of network devices (including Cisco, HP/Aruba, Juniper, Extreme, Brocade, and more), providing detailed insights into your network's composition.

When integrated with SIEMs (Elastic, Splunk, QRadar, etc.), NetVendor transforms from a static inventory tool into a **posture-change sensor** that enables proactive security monitoring and incident response.

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🔄 Common Workflows](#-common-workflows)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [📋 Quick Reference](#-quick-reference)
  - [Ways to Run NetVendor](#ways-to-run-netvendor)
  - [Expected Outputs](#expected-outputs)
- [📋 Detailed Usage](#-detailed-usage)
  - [Command-Line Flags](#command-line-flags)
  - [Offline Mode](#offline-mode)
  - [Historical Drift Analysis](#historical-drift-analysis)
  - [SIEM-Friendly Export](#siem-friendly-export)
  - [Windows Usage](#windows-usage)
  - [Verbose Output](#verbose-output)
  - [Runtime Logging](#runtime-logging)
- [📥 Supported Input Formats](#-supported-input-formats)
- [📊 Output Details](#-output-details)
- [🌟 Success Stories & Known Deployments](#-success-stories--known-deployments)
- [🔧 Advanced Topics](#-advanced-topics)
- [🧪 Testing & Quality](#-testing--quality)
- [📈 Project Status](#-project-status)

---

## ✨ Features

- **Multi-vendor MAC address parsing:** Supports Cisco, HP/Aruba, Juniper, Extreme, Brocade, and more.
- **Flexible input:** Accepts MAC address lists, MAC tables, and ARP tables in various formats.
- **Vendor identification:** Uses a local IEEE OUI cache for fast, secure lookups.
- **Comprehensive reporting:** Generates CSVs, summaries, and interactive HTML dashboards.
- **VLAN and port analysis:** Extracts and visualizes VLAN and port data where available.
- **Historical drift tracking:** Archive vendor summaries and analyze trends over time with metadata correlation.
- **SIEM integration:** Export normalized CSV/JSONL events for security monitoring and posture-change detection.
- **Extensible and robust:** Easily add support for new formats; thoroughly tested with real-world data.

---

## 🔄 Common Workflows

**Basic Analysis:**
```bash
python3 NetVendor.py input_file.txt
```
→ Generates standard outputs: Device CSV, Port CSV (if MAC table), HTML dashboard, Vendor Summary

**Offline Analysis (air-gapped networks):**
```bash
python3 NetVendor.py --offline input_file.txt
```
→ Uses only local OUI cache, no external API calls

**SIEM Integration:**
```bash
python3 NetVendor.py \
  --siem-export \
  --site DC1 \
  --environment prod \
  input_file.txt
```
→ Generates standard outputs + SIEM-ready CSV/JSONL files

**Historical Tracking with Drift Analysis:**
```bash
python3 NetVendor.py \
  --history-dir history \
  --site DC1 \
  --change-ticket CHG-12345 \
  --analyze-drift \
  input_file.txt
```
→ Generates standard outputs + archives summary with metadata + creates drift analysis CSV

**Complete Workflow (all features):**
```bash
python3 NetVendor.py \
  --offline \
  --history-dir history \
  --analyze-drift \
  --siem-export \
  --site DC1 \
  --environment prod \
  --change-ticket CHG-12345 \
  input_file.txt
```
→ Runs offline, generates all outputs, archives with metadata, creates drift analysis, and exports SIEM events

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Required packages: `requests`, `plotly`, `rich`, `tqdm`
- Input file containing MAC addresses or ARP data from your network devices

### Installation

```bash
git clone https://github.com/StewAlexander-com/NetVendor.git
cd NetVendor
pip install -e .
```

---

## 📋 Quick Reference

### Ways to Run NetVendor

**1. Simple Package Entry Point** (basic usage, no flags):
```bash
netvendor input_file.txt
# or
python3 -m netvendor input_file.txt
```
*Limited to basic analysis only - no advanced features*

**2. Standalone Script** (full feature set with all flags):
```bash
python3 NetVendor.py input_file.txt
```

**Important:** For all advanced features (offline mode, history tracking, SIEM export, drift analysis), use `python3 NetVendor.py`. The package entry point (`netvendor`) is a simple wrapper that only accepts an input file argument and does not support flags.

### Expected Outputs

NetVendor generates several output files in the `output/` directory:

- **Standard outputs** (always generated): Device CSV, Port CSV (for MAC tables), interactive HTML dashboard, and vendor summary text file
- **Optional outputs** (with flags): SIEM exports (CSV/JSONL), historical archives, and drift analysis CSV

See [Output Details](#-output-details) below for complete file descriptions.

---

## 📋 Detailed Usage

### Command-Line Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--offline` | Disable external vendor lookups (cache-only) | `--offline` |
| `--history-dir DIR` | Directory for archiving vendor summaries (created automatically if it doesn't exist) | `--history-dir history` |
| `--analyze-drift` | Run drift analysis on archived summaries | `--analyze-drift` |
| `--site SITE` | Site/region identifier for SIEM/drift metadata | `--site DC1` |
| `--environment ENV` | Environment identifier for SIEM exports | `--environment prod` |
| `--change-ticket ID` | Change ticket/incident ID for drift correlation | `--change-ticket CHG-12345` |
| `--siem-export` | Generate SIEM-friendly CSV/JSONL exports | `--siem-export` |

### Offline Mode

Use the `--offline` flag when you want to avoid any external vendor lookups (e.g., on air‑gapped networks). Devices that are not already present in the local OUI cache will appear as `Unknown`.

```bash
python3 NetVendor.py --offline input_file.txt
```

### Historical Drift Analysis

Track how vendor composition changes over time and correlate with change windows/incidents:

```bash
python3 NetVendor.py \
  --history-dir history \
  --site DC1 \
  --change-ticket CHG-12345 \
  --analyze-drift \
  input_file.txt
```

**What it does:**
- Creates the history directory if it doesn't exist
- Archives `vendor_summary.txt` to `history/vendor_summary-YYYYMMDD-HHMMSS.txt`
- Creates companion `.metadata.json` file with `run_timestamp`, `site`, `change_ticket_id`
- Generates `history/vendor_drift.csv` with metadata rows and vendor percentage trends

**SIEM Correlation:** The drift CSV metadata enables correlation with change windows and incidents, supporting 8D/5-why workflows. You can join drift data with SIEM events using `run_timestamp` and `site`, and correlate vendor mix shifts with `change_ticket_id`.

### SIEM-Friendly Export

For SIEM integration (Elastic, Splunk, etc.), generate normalized CSV and JSONL events:

```bash
python3 NetVendor.py \
  --siem-export \
  --site DC1 \
  --environment prod \
  input_file.txt
```

**Stable Schema** (all fields present in every record):

- `timestamp`: UTC ISO-8601 collection time (e.g., `2025-10-31T16:23:45Z`)
- `site`: Site/region identifier (e.g., `DC1`, `HQ`, `us-east-1`)
- `environment`: Environment identifier (e.g., `prod`, `dev`, `staging`)
- `mac`: Normalized MAC address (`xx:xx:xx:xx:xx:xx`)
- `vendor`: Vendor name from OUI lookup (or `Unknown` if not found)
- `device_name`: Device identifier (derived from MAC)
- `vlan`: VLAN ID (or `N/A` if not available)
- `interface`: Network interface/port identifier (e.g., `Gi1/0/1`, `ge-0/0/0`)
- `input_type`: Source data type (`mac_list`, `mac_table`, `arp_table`, `unknown`)
- `source_file`: Original input filename

**Correlation-friendly design:**
- All fields consistently named and present in every record
- MAC addresses normalized for reliable joins
- UTC ISO-8601 timestamps for time-based correlation
- Site and environment tags enable multi-site/environment dashboards

### Cross-Platform Compatibility

NetVendor is designed to work on **Linux (Debian/Ubuntu), macOS (Intel and Apple Silicon), and Windows**. All file operations use UTF-8 encoding and cross-platform path handling.

**Windows Usage:**
```powershell
# Set encoding environment variables (recommended)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
python3 NetVendor.py input_file.txt
```

**Linux/macOS Usage:**
```bash
python3 NetVendor.py input_file.txt
```

**Cross-Platform Considerations:**
- **File paths**: All paths use `pathlib.Path` for cross-platform compatibility (handles `/` vs `\` automatically)
- **File encoding**: All file operations explicitly use UTF-8 encoding to prevent encoding issues on Windows
- **Line endings**: Python's text mode handles both CRLF (Windows) and LF (Unix) automatically
- **File locking**: Cache writes use atomic operations (write to temp file, then rename) to prevent corruption if multiple processes run simultaneously
- **API timeouts**: All network requests have 5-second timeouts to prevent hangs on slow/unreliable networks
- **Error handling**: Permission errors and file system errors are handled gracefully on all platforms

### Verbose Output

Control debug output with the `NETVENDOR_VERBOSE` environment variable (only supported by `NetVendor.py`):

```bash
# Quiet mode (default)
python3 NetVendor.py input_file.txt

# Verbose mode - detailed processing information
NETVENDOR_VERBOSE=1 python3 NetVendor.py input_file.txt
```

When verbose mode is enabled, you'll see file type detection details, per-line processing information, sample device entries, CSV writing progress, and output file content preview.

### Runtime Logging

For troubleshooting and performance analysis, NetVendor can log runtime behavior to a structured log file:

```bash
# Enable runtime logging
NETVENDOR_LOG=1 python3 NetVendor.py input_file.txt
```

When enabled, a log file is created at `output/netvendor_runtime.log` in JSONL format (one JSON object per line). Each entry includes:
- `timestamp`: UTC ISO-8601 timestamp
- `event_type`: Type of event (e.g., "processing_start", "file_type_detection", "error")
- `event_data`: Event-specific data
- `context`: Additional context information

The logger captures key runtime events including file processing, error conditions, output generation, and performance metrics. Logging is disabled by default and has no performance impact when not enabled.

---

## 📥 Supported Input Formats

**Just paste your raw `show mac address-table` output into a file; NetVendor will auto-detect the format.** No heavy data cleaning required - the tool handles headers, whitespace, and various vendor formats automatically.

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
30      B8:AC:6F:77:88:99 DYNamic     1:1
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

**Format Detection Features:**
- Automatic file type detection based on content
- Flexible MAC parsing: Accepts colon, hyphen, dot, and mask/prefix formats
- VLAN extraction from multiple sources (column, interface, etc.)
- Port extraction for detailed switch analysis
- Header skipping and robust error handling

---

## 📊 Output Details

### Standard Outputs

![Security Dashboard](docs/images/security-dashboard.png?v=12.8)
*🔒 Device count analysis per VLAN - quickly identify VLANs with high device concentrations for security monitoring*

![Vendor Dashboard](docs/images/vendor-dashboard.png?v=12.8)
*📊 Comprehensive multi-panel VLAN analysis dashboard - view device counts, vendor diversity, heatmaps, and top vendor distributions across your network segments*

**Device Information CSV** (`{input_file}-Devices.csv`):
- One row per device
- Columns: MAC, Vendor, VLAN, Port
- Always generated

**Port Report CSV** (`{input_file}-Ports.csv`):
- Port utilization and device mapping
- Only generated for MAC address tables (not ARP or simple lists)
- Columns: Port, Total Devices, VLANs, Vendors, Device Details

**Vendor Distribution HTML** (`vendor_distribution.html`):
- Interactive dashboard with charts
- Vendor distribution pie chart
- VLAN analysis with multiple subplots
- Always generated

**Vendor Summary Text** (`vendor_summary.txt`):
- Plain text summary with vendor counts and percentages
- Formatted table for quick reference
- Always generated

### Optional Outputs

**SIEM Export Files** (requires `--siem-export`, written to `output/siem/` directory):
- `siem/netvendor_siem.csv`: Line-delimited CSV with header
- `siem/netvendor_siem.json`: JSONL format (one JSON object per line)
- Both contain identical data with stable schema for SIEM correlation

**History Archive Files** (requires `--history-dir`):
- `vendor_summary-YYYYMMDD-HHMMSS.txt`: Timestamped vendor summary snapshot
- `vendor_summary-YYYYMMDD-HHMMSS.metadata.json`: Companion metadata file with:
  - `run_timestamp`: UTC ISO-8601 timestamp
  - `site`: Site/region identifier
  - `change_ticket_id`: Change ticket/incident ID

**Drift Analysis CSV** (requires `--analyze-drift`):
- `history/vendor_drift.csv`: Vendor percentage trends across all archived runs
- Includes metadata rows at top: `run_timestamp`, `site`, `change_ticket_id`
- Vendor percentage rows showing changes over time

---

## 🌟 Success Stories & Known Deployments

NetVendor is used in production environments for network monitoring, security posture tracking, and asset management. While specific deployment details are kept confidential, the tool has been successfully deployed in:

- **Enterprise SOC environments**: Integrated with Elastic Stack and Splunk for continuous posture-change detection across multiple data centers
- **Network operations teams**: Daily analysis of MAC address tables from Cisco, Juniper, and Aruba switches to track device inventory and vendor distribution
- **Air-gapped networks**: Offline mode enables vendor identification in isolated environments without external API dependencies
- **Change management workflows**: Historical drift analysis with change ticket correlation supports incident response and root cause analysis

**Have a success story to share?** We'd love to hear how you're using NetVendor! Please open an issue or submit a pull request with your use case (anonymized as needed).

---

## 🔧 Advanced Topics

For detailed information on advanced topics, see **[ADVANCED.md](ADVANCED.md)**:

- **Posture-Change Detection & Security Monitoring**: SIEM integration workflows, correlation rules, and continuous monitoring strategies
- **Operational Best Practices**: Vendor lookup optimization, cache management, output organization, troubleshooting, and cross-platform considerations
- **Runtime Considerations**: Performance benchmarks, network behavior, disk space planning, and error handling details

---

## 🧪 Testing & Quality

- Run tests:
```bash
pytest -q
```

- Optional linting/type checks (if configured locally):
```bash
ruff check .
mypy netvendor
```

- Sample inputs for validation are in `tests/data/`.

---

## 📈 Project Status

**Latest Release: [v12.8](https://github.com/StewAlexander-com/NetVendor/releases/tag/v12.8)** - Enhanced HTML Dashboard Readability

NetVendor is actively maintained and regularly updated.  
**Recent improvements:**
- ✅ Enhanced MAC address parsing for Juniper, Aruba, Extreme, Brocade, and more
- ✅ Improved OUIManager logic and normalization
- ✅ Real-world OUI test coverage
- ✅ Historical drift analysis with metadata correlation (timestamp, site, change_ticket_id)
- ✅ SIEM export with stable schema for posture-change detection (CSV/JSONL in `output/siem/`)
- ✅ Runtime logging for troubleshooting and performance analysis (JSONL format)
- ✅ Enhanced error handling with user-friendly messages and actionable hints
- ✅ Offline mode support for air-gapped networks (`--offline` flag)
- ✅ Comprehensive README with TL;DR, workflows, table of contents, and quick-start examples
- ✅ All tests pass and program output confirmed

**Planned:**
- More vendor format support
- Additional visualization options
- Network topology mapping

---

## 🤝 Contributing

Contributions are welcome! Please open issues or submit pull requests.

## 📄 License

MIT License

## 👤 Author

Stewart Alexander

---

**💡 Tip:** For best results, always use the latest OUI cache and keep your dependencies up to date. And remember: Networks are more fun when you know who's on them! 😄
