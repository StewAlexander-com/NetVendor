# 🔍 ShadowVendor Technical Tutorial

**A Deep Dive into How ShadowVendor Works**

## Audience & Goals

This tutorial is designed for:

- **Contributors**: Developers who want to modify parsers, add features, or extend functionality
- **SOC Engineers**: Security professionals who need to understand behavior in production, trust offline mode, and integrate with SIEM systems
- **Network Engineers**: Professionals evaluating the tool for enterprise deployment who need to understand reliability and operational characteristics

**After reading this tutorial, you should be able to:**
- Understand the complete data flow from input file to output generation
- Modify parsers to support new MAC table formats
- Trust the tool's behavior in production (offline mode, atomic writes, error handling)
- Debug issues by knowing which components to inspect
- Extend functionality by understanding extension points
- Integrate ShadowVendor into SIEM workflows with confidence

---

## 🗺️ Quick Reference

**If you're here to...**

- **Understand the big picture** → Start with [What ShadowVendor Does](#what-shadowvendor-does) and [Architecture Overview](#architecture-overview)
- **See how data flows** → Read [Processing Pipeline](#processing-pipeline) and [Execution Flow](#execution-flow)
- **Understand vendor lookups** → Jump to [Vendor Lookup System](#vendor-lookup-system) and [OUI Cache Management](#oui-cache-management)
- **Modify or extend code** → See [For Contributors](#for-contributors) and [Extension Points](#extension-points)
- **Debug issues** → Check [Debugging Playbook](#debugging-playbook)
- **Add tests** → Review [Test Strategy](#test-strategy)

### ⚡ If You Only Have 5 Minutes

**Quick path for contributors:** Read [Architecture Overview](#architecture-overview) → [Processing Pipeline](#processing-pipeline) → Run `pytest -q` to see existing tests → Make your changes → Run `pytest tests/test_shadowvendor.py -v` (or relevant test file) to verify. This gives you the essential context and validation workflow without diving into every detail.

---

## 📑 Table of Contents

1. [Overview](#overview)
   - [What ShadowVendor Does](#what-shadowvendor-does)
   - [Architecture Overview](#architecture-overview)
   - [Design Philosophy](#design-philosophy)
2. [How It Works](#how-it-works)
   - [Processing Pipeline](#processing-pipeline)
   - [Execution Flow](#execution-flow)
   - [Core Components](#core-components)
   - [OUI Cache Management](#oui-cache-management)
3. [For Contributors](#for-contributors)
   - [Getting Started](#getting-started)
   - [Extension Points](#extension-points)
   - [Test Strategy](#test-strategy)
4. [Troubleshooting](#troubleshooting)
   - [Debugging Playbook](#debugging-playbook)

---

## Overview

### What ShadowVendor Does

ShadowVendor is a network analysis tool that transforms raw network device outputs (MAC address tables, ARP tables, or simple MAC lists) into structured, actionable intelligence. At its core, it:

1. **Parses** network device outputs from multiple vendors (Cisco, Juniper, HP/Aruba, Extreme, Brocade, etc.)
2. **Normalizes** MAC addresses to a consistent format (`xx:xx:xx:xx:xx:xx`)
3. **Identifies** device vendors using IEEE OUI (Organizationally Unique Identifier) lookups
4. **Extracts** network context (VLANs, ports, interfaces)
5. **Generates** multiple output formats (CSV, HTML dashboards, text summaries)
6. **Enables** advanced features like historical drift analysis and SIEM integration

#### Core Data Transformation

```
Raw Network Output → Parsed Devices → Vendor-Enriched Data → Multiple Output Formats
```

**Input Example:**
```
Vlan    Mac Address       Type        Ports
10      0011.2233.4455    DYNAMIC     Gi1/0/1
20      00:0E:83:11:22:33 DYNAMIC     ge-0/0/0
```

**Output:**
- Device CSV with vendor information
- Interactive HTML dashboard
- Port utilization reports
- Vendor distribution summaries

---

### Architecture Overview

ShadowVendor follows a modular architecture with clear separation of concerns:

```
ShadowVendor.py (Main Entry Point)
    │
    ├── shadowvendor/core/
    │   ├── shadowvendor.py          # Core parsing logic
    │   └── oui_manager.py           # Vendor lookup system
    │
    └── shadowvendor/utils/
        ├── vendor_output_handler.py  # CSV, HTML, text generation
        ├── drift_analysis.py         # Historical analysis
        ├── siem_export.py            # SIEM event generation
        └── runtime_logger.py         # Structured logging
```

**Key Design Principles:**
- **Separation of concerns**: Parsing, lookup, and output generation are separate modules
- **Single responsibility**: Each module has one clear purpose
- **Dependency injection**: OUI manager is passed to output handlers, enabling testing and offline mode

---

### Design Philosophy

ShadowVendor prioritizes **reliability**, **performance**, and **operational safety** over convenience features. Key design decisions:

| Design Decision | Rationale | Tradeoff |
|----------------|-----------|----------|
| **Offline-first OUI cache** | Enables air-gapped operation, ensures consistent results | Initial cache population required |
| **Atomic file writes** | Prevents corruption if process is interrupted | Slightly more complex than direct writes |
| **Rate-limited API lookups** | Respects API service limits, prevents throttling | Adds latency for uncached lookups |
| **Multi-tier vendor lookup** | Cache-first strategy maximizes speed and reliability | Complex state management |
| **Vendor-agnostic parsing** | Pattern matching handles diverse formats | May misclassify edge cases |
| **Cross-platform compatibility** | `pathlib.Path` and UTF-8 encoding work everywhere | Must test on all platforms |

**Philosophy Summary**: ShadowVendor prioritizes **reliability** (offline-first, atomic operations), **performance** (caching, rate limiting), and **operational safety** (error handling, cross-platform compatibility) over convenience features that could compromise production readiness.

---

## How It Works

### Processing Pipeline

**Data Flow Diagram:** *This diagram shows how a single input file transforms into multiple outputs through normalization, vendor enrichment, and parallel output generation.*

```
┌─────────────────┐
│  Input File     │
│  (MAC/ARP data) │
└────────┬────────┘
         │
         ▼
┌────────────────-─┐
│ File Type        │
│ Detection        │
└────────┬────────-┘
         │
         ▼
┌────────────────-─┐
│ Line-by-Line     │
│ Parsing          │
└────────┬───────-─┘
         │
         ▼
┌───────────────-──┐
│ MAC Address      │
│ Normalization    │
└────────┬───────-─┘
         │
         ▼
┌───────────────-──┐
│ Device Dictionary│
│ {mac: {vlan,     │
│       port}}     │
└────────┬───────-─┘
         │
         ▼
┌──────────────-───┐
│ Vendor Lookup    │
│ (OUIManager)     │
│ Cache → API      │
└────────┬───────-─┘
         │
         ▼
┌────────────────-─-┐
│ Enriched Devices  │
│ {mac: {vlan,      │
│       port,       │
│       vendor}}    │
└────────┬───────--─┘
         │
         ├──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Device CSV   │ │ HTML         │ │ Text         │ │ SIEM Export  │
│              │ │ Dashboard    │ │ Summary      │ │ (optional)   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Processing Steps:**

1. **Entry Point** (`ShadowVendor.py`): Parses CLI arguments, initializes logger and OUI manager
2. **File Type Detection**: Reads first 2 lines to determine format (MAC list, ARP table, or MAC table)
3. **Line-by-Line Parsing**: Extracts MAC addresses, VLANs, and ports based on detected format
4. **MAC Normalization**: Converts all MAC formats to `xx:xx:xx:xx:xx:xx`
5. **Vendor Lookup**: Enriches devices with vendor information via OUI lookup
6. **Output Generation**: Creates CSV, HTML, text, and optionally SIEM exports in parallel

---

### Execution Flow

This section walks through the complete execution flow from code start to output generation.

#### Step 1: Entry Point and Initialization

**File**: `ShadowVendor.py`

```python
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    
    # Initialize runtime logger
    logger = get_logger()
    
    # Initialize OUI manager (with offline flag if specified)
    oui_manager = OUIManager(offline=args.offline)
```

**Why**: The main script handles CLI argument parsing, logging initialization, and sets up the OUI manager. The `OUIManager` is initialized early because it loads caches that may take a moment.

#### Step 2: File Type Detection

**File**: `ShadowVendor.py` (lines 271-296)

```python
with open(input_file, 'r', encoding='utf-8') as f:
    first_line = f.readline().strip()
    second_line = f.readline().strip() if first_line else ""
    
    # Determine file type
    is_mac_list = is_mac_address(first_line)
    is_arp_table = not is_mac_list and (
        first_line.startswith("Protocol") or
        "Internet" in first_line or
        "Internet" in second_line
    )
    is_mac_table = not is_mac_list and not is_arp_table
```

**How it works**:
1. Reads first two lines to peek at file structure
2. Checks if first line is a valid MAC address → `mac_list`
3. Checks for ARP table headers/keywords → `arp_table`
4. Defaults to `mac_table` if neither matches

**Why this approach**: 
- **Fast**: Only reads 2 lines for detection
- **Robust**: Handles files that start with headers or data
- **Flexible**: Works even if headers are slightly different

#### Step 3: Line-by-Line Parsing

**File**: `ShadowVendor.py` (lines 327-390)

The parsing logic differs based on detected file type:

**MAC List Processing:**
```python
if is_mac_list:
    mac = line.lower()
    if is_mac_address(mac):
        mac_formatted = format_mac_address(mac)
        if mac_formatted:
            devices[mac_formatted] = {'vlan': 'N/A', 'port': 'N/A'}
```

**ARP Table Processing:**
```python
elif is_arp_table:
    parts = line.split(None, 5)  # Split into max 6 parts
    if len(parts) >= 6 and parts[0] == "Internet":
        mac = parts[3].strip()  # Hardware address is 4th field
        interface = parts[5].strip()  # Interface is last field
        
        mac_formatted = format_mac_address(mac)
        if mac_formatted:
            vlan = (
                interface.replace('Vlan', '')
                if 'Vlan' in interface else 'N/A'
            )
            devices[mac_formatted] = {'vlan': vlan, 'port': 'N/A'}
```

**MAC Table Processing:**
```python
else:  # MAC table
    parts = line.split(None, 4)  # Preserve spacing
    if len(parts) >= 4:
        try:
            vlan = str(int(parts[0]))  # Validate VLAN is numeric
            mac = parts[1]
            port = parts[3]
            
            mac_formatted = format_mac_address(mac)
            if mac_formatted:
                devices[mac_formatted] = {'vlan': vlan, 'port': port}
```

**Key Design Decisions**:
- **Dictionary as data structure**: `devices[mac] = {vlan, port}` allows deduplication (last occurrence wins)
- **Normalized MACs as keys**: Ensures consistent lookups regardless of input format
- **Graceful error handling**: Invalid lines are skipped, processing continues

---

### Core Components

#### File Type Detection

ShadowVendor uses multiple heuristics to detect file types. The detection functions are in `shadowvendor/core/shadowvendor.py`:

**MAC Address Validation** (`is_mac_address()`):
- Supports all common MAC formats (colon, hyphen, dot, mask formats)
- Validates hex characters, not just format
- Handles vendor-specific formats (Cisco dots, Juniper masks, etc.)

**ARP Table Detection** (`is_arp_table()`):
- Checks for header patterns ("Protocol", "Address", "Hardware Addr")
- Validates data line structure (6 fields with "Internet" as first field)
- Verifies MAC address format in hardware address field

**MAC Table Detection** (`is_mac_address_table()`):
- Uses multiple header patterns for different vendors
- Validates VLAN number (1-4094 range)
- Ensures MAC address follows VLAN in data lines

#### MAC Address Normalization

**File**: `shadowvendor/core/shadowvendor.py` (lines 94-119)

```python
def format_mac_address(mac: str) -> str:
    """
    Format a MAC address consistently.
    Input can be any format, output will be xx:xx:xx:xx:xx:xx
    Handles all vendor-specific formats including masks.
    """
    if not mac:
        return None
    
    # Split on common separators to handle mask formats
    parts = re.split(r'[/\s]', mac.strip())
    mac_part = parts[0]
    
    # Handle dot notation (ARP table format)
    if '.' in mac_part:
        parts = mac_part.strip().split('.')
        mac_clean = ''.join(parts)[:12]
    else:
        # Handle standard formats
        mac_clean = mac_part.strip().lower().replace(':', '').replace('-', '')
    
    # Take first 12 characters and format with colons
    if len(mac_clean) >= 12:
        mac_clean = mac_clean[:12]
        return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
    return None
```

**Example Transformations**:

| Input Format | Output |
|--------------|--------|
| `0011.2233.4455` | `00:11:22:33:44:55` |
| `00:11:22:33:44:55` | `00:11:22:33:44:55` |
| `00-11-22-33-44-55` | `00:11:22:33:44:55` |
| `001122334455` | `00:11:22:33:44:55` |
| `00:11:22:33:44:55/ff:ff:ff:ff:ff:ff` | `00:11:22:33:44:55` |

**Why normalization**:
- **Consistency**: All MACs in output use same format
- **Deduplication**: Same device with different input formats becomes one entry
- **Lookup efficiency**: OUI cache uses normalized format as keys

---

### Vendor Lookup System

The `OUIManager` class is the heart of vendor identification. It implements a multi-tier lookup strategy:

```
1. Check failed_lookups set
   └─> If found: Return None (don't retry failed lookups)
   
2. Check in-memory cache
   └─> If found: Return vendor name
   
3. If offline mode: Add to failed_lookups, return None
   
4. Try API lookup (with rate limiting and retries)
   ├─> Success: Cache result, return vendor
   └─> Failure: Add to failed_lookups, return None
```

#### Architecture

**File**: `shadowvendor/core/oui_manager.py`

```python
class OUIManager:
    def __init__(self, oui_file: str = None, offline: bool = False):
        self.oui_file = oui_file
        self.offline = offline
        self.cache = {}  # In-memory cache
        self.failed_lookups = set()  # Track failed lookups
        
        # Setup cache directories
        self.output_dir = Path("output")
        self.data_dir = self.output_dir / "data"
        self.cache_file = self.data_dir / "oui_cache.json"
        self.failed_lookups_file = self.data_dir / "failed_lookups.json"
        
        # Load caches
        self.load_preseeded_cache()  # Wireshark manufacturers database
        if self.cache_file.exists():
            self.load_cache()  # User's previous lookups
        if self.failed_lookups_file.exists():
            self.load_failed_lookups()
```

#### OUI Normalization

**File**: `shadowvendor/core/oui_manager.py` (lines 211-217)

```python
def _normalize_mac(self, mac: str) -> str:
    """Normalize MAC address format for lookups."""
    # Remove any separators and convert to uppercase
    mac = re.sub(r'[.:-]', '', mac.upper())
    # Keep only first 6 characters (OUI portion) and format with colons
    oui = mac[:6]
    return f"{oui[:2]}:{oui[2:4]}:{oui[4:]}"
```

**Example**: `00:11:22:33:44:55` → `00:11:22` (OUI portion)

**Why**: The first 6 hex characters (3 bytes) of a MAC address are the OUI, which identifies the vendor. The remaining 6 characters are device-specific.

#### API Lookup with Rate Limiting

**File**: `shadowvendor/core/oui_manager.py` (lines 256-302)

The system implements service rotation, rate limiting, exponential backoff, and failure tracking:

```python
# Try API lookup
original_service_index = self.current_service_index
retries = 0
max_retries = len(self.api_services) * 2

while retries < max_retries:
    service = self.api_services[self.current_service_index]
    
    try:
        self._rate_limit(service)  # Enforce rate limit
        url = service['url'].format(oui=oui)
        response = requests.get(
            url, headers=service['headers'], timeout=5
        )
        
        if response.status_code == 200:
            # Parse response based on service
            if service['name'] == 'maclookup':
                data = response.json()
                vendor = data.get('company', 'Unknown')
            else:
                vendor = response.text.strip()
            
            if vendor and vendor != "Unknown":
                self.cache[oui] = vendor
                self.save_cache()
                return vendor
                
        elif response.status_code == 429:  # Rate limit
            service['rate_limit'] *= 1.5  # Increase backoff
            
        elif response.status_code == 404:  # Not found
            self.failed_lookups.add(oui)
            self.save_failed_lookups()
            return None

    except (requests.RequestException, json.JSONDecodeError):
        pass  # Try next service

    # Rotate to next service
    self.current_service_index = (
        self.current_service_index + 1
    ) % len(self.api_services)
    retries += 1
    
    # Wait before retry cycle
    if self.current_service_index == original_service_index:
        time.sleep(1)

# If all retries failed
self.failed_lookups.add(oui)
self.save_failed_lookups()
return None
```

**Key Features**:
- **Service Rotation**: Tries multiple API services (macvendors.com, maclookup.app)
- **Rate Limiting**: Enforces delays between API calls to respect rate limits
- **Exponential Backoff**: Increases delay on rate limit errors
- **Timeout Protection**: 5-second timeout prevents hangs
- **Failure Tracking**: Records failed lookups to avoid retries

#### Cache Persistence

**File**: `shadowvendor/core/oui_manager.py` (lines 157-178)

The cache uses atomic writes to prevent corruption:

```python
def save_cache(self):
    """Save only user-added cache entries with atomic write."""
    try:
        # Use atomic write pattern: write to temp file, then rename
        temp_file = self.cache_file.with_suffix('.tmp')
        with temp_file.open('w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())  # Force write to disk
            except (AttributeError, OSError):
                pass
        # Atomic rename (works on Unix and Windows)
        temp_file.replace(self.cache_file)
    except (IOError, OSError, PermissionError) as e:
        # Fallback: direct write if atomic rename fails
        try:
            with self.cache_file.open('w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except (IOError, OSError, PermissionError):
            pass  # Silently fail if cache can't be saved
```

**Why atomic writes**:
- **Prevents corruption**: If process is interrupted, cache file isn't left in partial state
- **Cross-platform**: Works on Windows, Linux, macOS
- **Thread-safe**: Multiple processes can run without corrupting cache

---

### OUI Cache Management

This section details how the OUI JSON cache (`output/data/oui_cache.json`) is loaded, used, and updated throughout ShadowVendor's execution.

#### Cache Lifecycle

1. **Initialization**: Cache is loaded into memory when `OUIManager` is created
2. **Lookup**: Vendor queries check the in-memory cache first
3. **Enrichment**: New vendor lookups are added to the cache
4. **Persistence**: Cache is saved to disk using atomic writes

#### Step-by-Step Cache Flow

**Step 1: OUIManager Initialization**

```python
# Location: shadowvendor/core/oui_manager.py, lines 34-65
def __init__(self, oui_file: str = None, offline: bool = False):
    # 1. Set instance variables
    self.cache = {}  # In-memory cache dictionary
    self.failed_lookups = set()
    
    # 2. Setup cache directory structure
    self.output_dir = Path("output")
    self.data_dir = self.output_dir / "data"
    self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Define cache file paths
    self.cache_file = self.data_dir / "oui_cache.json"
    
    # 4. Load pre-seeded cache (if provided)
    self.load_preseeded_cache()
    
    # 5. Load user's JSON cache
    if self.cache_file.exists():
        self.load_cache()
```

**Step 2: Loading the JSON Cache**

```python
# Location: shadowvendor/core/oui_manager.py, lines 147-155
def load_cache(self):
    """Load user's cached vendor lookups."""
    try:
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            user_cache = json.load(f)  # Parse JSON into dictionary
            self.cache.update(user_cache)
    except (json.JSONDecodeError, IOError):
        pass  # Silently fail if cache doesn't exist or is corrupted
```

**What happens:**
- Opens `output/data/oui_cache.json` for reading
- Parses JSON content into a Python dictionary
- Updates `self.cache` with all entries from the file
- If file doesn't exist or is corrupted, cache remains empty (no error)

**Example JSON cache structure:**
```json
{
  "00:11:22": "Cisco Systems, Inc.",
  "00:0E:83": "Hewlett Packard",
  "00:1B:44": "Huawei Technologies Co., Ltd.",
  "00:50:56": "VMware, Inc."
}
```

**Step 3: Vendor Lookup During Output Generation**

When generating outputs, each function calls `oui_manager.get_vendor(mac)`:

```python
# CSV Generation example
for mac, info in devices.items():
    vendor = oui_manager.get_vendor(mac)  # Lookup vendor from cache
    vendor = vendor if vendor is not None else "Unknown"
    writer.writerow([mac, vendor, vlan, port])
```

**Step 4: Cache Update on New Vendor Discovery**

When a new vendor is discovered via API:

```python
# Location: shadowvendor/core/oui_manager.py, lines 276-280
if vendor and vendor != "Unknown":
    # Cache the result
    self.cache[oui] = vendor
    self.save_cache()  # Persist to JSON file
    return vendor
```

#### Process Flow Diagram

```
┌──────────────────────────────────────────────┐
│   SHADOWVENDOR EXECUTION START               │
└──────────────────┬───────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  Step 1: Initialize OUIManager               │
│  oui_manager = OUIManager(offline=...)       │
└──────────────────┬───────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  Step 2: Setup Cache Directory               │
│  • Creates output/data/ directory            │
│  • Sets cache_file = oui_cache.json          │
└──────────────────┬───────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  Step 3: Load JSON Cache from Disk           │
│  IF oui_cache.json EXISTS:                   │
│    • Open file for reading                   │
│    • json.load() → parse JSON                │
│    • self.cache.update(user_cache)           │
│    • Merge with pre-seeded cache             │
└──────────────────┬───────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────-┐
│  Step 4: Process Input File                   │
│  • Parse MAC addresses                        │
│  • Build devices dict: {mac: {vlan, port}}    │
└──────────────────┬───────────────────────────-┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  Step 5: Generate Outputs                    │
│  For each MAC:                               │
│    vendor = oui_manager.get_vendor(mac)      │
│    ┌────────────────────────────────────┐    │
│    │  get_vendor() Lookup:              │    │
│    │  1. Normalize MAC → Extract OUI    │    │
│    │  2. Check failed_lookups           │    │
│    │  3. Check cache (self.cache)       │◄── │
│    │  4. IF not found: Try API lookup  │     │
│    │  5. IF API success: Cache result   │    │
│    └────────────────────────────────────┘    │
└──────────────────┬───────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  Step 6: Cache Persistence                   │
│  save_cache()                                │
│  • Create temp file: oui_cache.json.tmp      │
│  • json.dump(self.cache, f)                  │
│  • Atomic rename: .tmp → .json               │
└──────────────────┬───────────────────────────┘
                    │
                    ▼
            EXECUTION COMPLETE
```

#### Cache Data Flow Summary

**Cache Loading (Startup):**
```
Disk (oui_cache.json) → JSON Parser → Python Dictionary (self.cache) → In-Memory Lookups
```

**Cache Usage (Runtime):**
```
MAC Address → OUI Normalization → Dictionary Lookup (self.cache[oui]) → Vendor Name → Output Files
```

**Cache Persistence (Updates):**
```
API Lookup → New Vendor → self.cache[oui] = vendor → JSON Serialization → Atomic Write → Disk
```

#### Key Implementation Details

**1. Cache Structure:**
- **Format**: JSON object with OUI as keys, vendor names as values
- **OUI Format**: `"00:11:22"` (6 hex characters with colons)
- **Location**: `output/data/oui_cache.json`
- **Encoding**: UTF-8

**2. Cache Loading Priority:**
1. Pre-seeded cache (Wireshark database, if provided)
2. User cache (`oui_cache.json`) - overrides pre-seeded entries
3. Failed lookups (`failed_lookups.json`) - prevents retries

**3. Cache Update Strategy:**
- **Lazy Loading**: Cache is only updated when new vendors are discovered via API
- **Atomic Writes**: Prevents corruption if process is interrupted
- **Full Cache Save**: Entire cache dictionary is saved (not incremental)

**4. Cache Lookup Performance:**
- **Time Complexity**: O(1) - Dictionary lookup is constant time
- **Memory**: Entire cache loaded into RAM for fast access
- **Network**: No network calls if OUI is cached (offline-capable)

**5. Cache File Format Example:**
```json
{
  "00:11:22": "Cisco Systems, Inc.",
  "00:0E:83": "Hewlett Packard",
  "00:1B:44": "Huawei Technologies Co., Ltd.",
  "00:50:56": "VMware, Inc.",
  "00:AA:00": "Intel Corporate"
}
```

#### Integration Points

The OUI cache is used by these components:

1. **CSV Generation** (`vendor_output_handler.py::make_csv()`)
   - Calls `oui_manager.get_vendor(mac)` for each device
   - Writes vendor to CSV output

2. **HTML Dashboard** (`vendor_output_handler.py::create_vendor_distribution()`)
   - Aggregates vendors from cache lookups
   - Creates pie charts and bar charts

3. **Text Summary** (`vendor_output_handler.py::save_vendor_summary()`)
   - Counts vendors from cache lookups
   - Generates statistics

4. **Port Report** (`vendor_output_handler.py::generate_port_report()`)
   - Groups vendors by port using cache lookups

5. **SIEM Export** (`siem_export.py::export_siem_events()`)
   - Includes vendor information from cache in SIEM events

---

### Output Generation

ShadowVendor generates multiple output formats, each serving different use cases:

#### Device CSV Generation

**File**: `shadowvendor/utils/vendor_output_handler.py` (lines 26-67)

```python
def make_csv(input_file: Union[Path, str], devices: Dict[str, Dict[str, str]], oui_manager: OUIManager) -> None:
    """Creates a CSV file with device information."""
    output_file = output_dir / f"{input_file.stem}-Devices.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
        
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vendor = vendor if vendor is not None else "Unknown"
            vlan = info.get('vlan', 'N/A')
            port = info.get('port', 'N/A')
            writer.writerow([mac, vendor, vlan, port])
```

#### HTML Dashboard Generation

**File**: `shadowvendor/utils/vendor_output_handler.py` (lines 134-391)

The HTML dashboard uses Plotly to create interactive visualizations with vendor distribution charts, VLAN analysis, and port utilization heatmaps.

#### Port Report Generation

**File**: `shadowvendor/utils/vendor_output_handler.py` (lines 69-132)

Generates CSV reports analyzing devices connected to each network port, including total devices, VLANs, and vendors per port.

#### Advanced Features

- **Historical Drift Analysis**: Tracks vendor distribution changes over time
- **SIEM Export**: Creates normalized events for security monitoring with stable schema

---

## For Contributors

### Getting Started

**If you want to contribute code, read these sections first:**

1. **[Architecture Overview](#architecture-overview)** - Understand the modular structure
2. **[Processing Pipeline](#processing-pipeline)** - See how data flows through the system
3. **[Vendor Lookup System](#vendor-lookup-system)** - Core OUI management logic
4. **[Output Generation](#output-generation)** - How outputs are created

**Then:**
- Run `pytest -q` to see existing tests
- Look at `tests/data/` for sample input files
- Review `tests/test_shadowvendor.py` for parsing tests
- Check `tests/test_oui_manager.py` for vendor lookup tests

---

### Extension Points

This section provides step-by-step guides for extending ShadowVendor's functionality.

#### Adding a New MAC-Table Vendor Format

**When**: You encounter a switch vendor whose MAC table format isn't recognized.

**Steps**:

1. **Add header pattern** in `shadowvendor/core/shadowvendor.py`, function `is_mac_address_table()`:
   ```python
   header_patterns = [
       # ... existing patterns ...
       ["VLAN", "MAC", "Type", "YourVendorHeader"],  # Add your pattern
   ]
   ```

2. **Test detection** by adding a test case in `tests/test_shadowvendor.py`:
   ```python
   def test_your_vendor_format():
       assert is_mac_address_table("VLAN MAC Type YourVendorHeader")
   ```

3. **Verify parsing** - The existing parsing logic in `ShadowVendor.py` should handle most formats, but if your vendor uses a different column order, modify the parsing logic there.

4. **Run tests**: `pytest tests/test_shadowvendor.py::test_your_vendor_format -v`

**Files to modify**: `shadowvendor/core/shadowvendor.py`, `tests/test_shadowvendor.py`

#### Adding Another OUI API Backend

**When**: You want to add a fallback API service or replace an existing one.

**Steps**:

1. **Add service configuration** in `shadowvendor/core/oui_manager.py`, `__init__()` method:
   ```python
   self.api_services = [
       # ... existing services ...
       {
           'name': 'your_api',
           'url': 'https://api.example.com/{oui}',
           'headers': {'Authorization': 'Bearer YOUR_KEY'},  # If needed
           'rate_limit': 1.0,  # Seconds between calls
           'last_call': 0
       }
   ]
   ```

2. **Add response parsing** in `get_vendor()` method (around line 270):
   ```python
   if service['name'] == 'your_api':
       data = response.json()  # Or response.text, depending on format
       vendor = data.get('vendor_name', 'Unknown')
   ```

3. **Test with offline mode disabled** to verify API integration.

**Files to modify**: `shadowvendor/core/oui_manager.py`

#### Adding a New Output Type

**When**: You want to generate a different output format (e.g., JSON, XML, database export).

**Steps**:

1. **Create new function** in `shadowvendor/utils/vendor_output_handler.py`:
   ```python
   def generate_your_format(devices: Dict, oui_manager: OUIManager, input_file: Path) -> None:
       """Generate your custom output format."""
       output_file = Path("output") / f"{input_file.stem}.yourformat"
       # Your generation logic here
   ```

2. **Call from main script** in `ShadowVendor.py`, after other output generation:
   ```python
   from shadowvendor.utils.vendor_output_handler import generate_your_format
   # ... existing outputs ...
   generate_your_format(devices, oui_manager, input_file)
   ```

3. **Add tests** in `tests/test_vendor_output_handler.py`:
   ```python
   def test_generate_your_format(temp_output_dir, sample_device_data, monkeypatch):
       # Test your format generation
   ```

**Files to modify**: `shadowvendor/utils/vendor_output_handler.py`, `ShadowVendor.py`, `tests/test_vendor_output_handler.py`

---

### Test Strategy

ShadowVendor's test suite provides comprehensive coverage. This section explains how the testing process works, from running tests to understanding results.

#### Understanding the Test Process

**What happens when you run tests:**

1. **Test Discovery**: pytest automatically finds all test files (files starting with `test_`) and test functions (functions starting with `test_`)
2. **Fixture Setup**: Before each test, pytest runs fixtures (like `temp_dir`, `sample_mac_table_file`) to set up test data
3. **Test Execution**: Each test function runs in isolation with its own temporary directory
4. **Assertion Validation**: Tests use `assert` statements to verify expected behavior
5. **Cleanup**: Temporary files and directories are automatically cleaned up after each test

**Test isolation**: Each test runs in its own temporary directory (`tempfile.TemporaryDirectory()`), so tests don't interfere with each other or pollute your workspace.

#### Test Structure

```
tests/
├── __init__.py
├── conftest.py                      # Shared fixtures (temp_dir, sample files)
├── test_execution_paths.py         # All execution paths (20+ tests)
├── test_shadowvendor.py            # Parsing and format detection tests
├── test_oui_manager.py              # Vendor lookup and caching tests
├── test_vendor_output_handler.py    # Output generation tests
├── test_api.py                      # Python API tests
└── data/                            # Sample input files
    ├── test-mac-list.txt            # 100 MAC addresses
    ├── test-mac-table.txt           # 500+ MAC table entries
    └── test-arp-table.txt           # ARP table format
```

#### Running Tests

**Basic test execution:**

```bash
# Run all tests (quick summary)
pytest -q

# Run all tests (verbose - shows each test name)
pytest -v

# Run execution path tests (comprehensive validation)
pytest tests/test_execution_paths.py -v

# Run specific test file
pytest tests/test_shadowvendor.py -v

# Run specific test function
pytest tests/test_shadowvendor.py::test_is_mac_address -v

# Run with coverage report (shows which code is tested)
pytest --cov=shadowvendor --cov-report=html
```

**Understanding test output:**

- **PASSED**: Test completed successfully, all assertions passed
- **FAILED**: An assertion failed or an exception occurred
- **SKIPPED**: Test was skipped (e.g., missing optional dependency)
- **ERROR**: Test setup/fixture failed before test could run

#### Writing New Tests

**Step-by-step guide for adding a new test:**

1. **Identify what to test**: Decide what functionality needs validation
   - New parser format? → Add to `test_shadowvendor.py`
   - New execution path? → Add to `test_execution_paths.py`
   - New output format? → Add to `test_vendor_output_handler.py`

2. **Create test data** (if needed):
   ```python
   @pytest.fixture
   def my_test_file(temp_dir):
       test_file = temp_dir / "my_input.txt"
       test_file.write_text("... test data ...")
       return test_file
   ```

3. **Write the test function**:
   ```python
   def test_my_feature(my_test_file, temp_dir):
       """Test: Description of what this test validates."""
       # Setup
       from ShadowVendor import main
       
       # Execute
       with patch('sys.argv', ['ShadowVendor.py', str(my_test_file)]):
           main()
       
       # Verify
       assert (temp_dir / "output" / "vendor_summary.txt").exists()
       # Add more assertions as needed
   ```

4. **Run the test**:
   ```bash
   pytest tests/test_my_file.py::test_my_feature -v
   ```

5. **Verify it passes**: Test should show `PASSED` status

**Test best practices:**
- **One assertion per concept**: Test one thing at a time
- **Descriptive names**: Test function names should explain what they test
- **Use fixtures**: Reuse test data setup via fixtures
- **Clean assertions**: Verify both that code runs AND produces correct outputs
- **Test edge cases**: Don't just test the happy path

#### Security Testing with Bandit

ShadowVendor includes **Bandit** security scanning to detect potential security vulnerabilities and code execution risks.

**Running security scans:**
```bash
# Install development dependencies (includes bandit)
pip install -r requirements-dev.txt

# Run security scan
bandit -c bandit.yaml -r shadowvendor/ ShadowVendor.py

# Generate JSON report for CI/CD integration
bandit -c bandit.yaml -r shadowvendor/ ShadowVendor.py -f json -o bandit-report.json
```

**What Bandit checks:**
- SQL injection vulnerabilities
- Command injection risks (subprocess usage)
- Insecure cryptographic functions
- Hardcoded passwords and secrets
- Insecure random number generation
- Code execution vulnerabilities
- And other security anti-patterns

**Configuration**: The `bandit.yaml` file configures which tests to skip (false positives for intentional patterns) and which directories to exclude from scanning.

**Current status**: ✅ No security issues identified (with configured exclusions for intentional patterns like graceful error handling and trusted subprocess usage).

For detailed security testing information, see **[TEST_COVERAGE.md](TEST_COVERAGE.md#security-testing)**.

For detailed test coverage information, see **[TEST_COVERAGE.md](TEST_COVERAGE.md)** and **[EXECUTION_PATHS.md](EXECUTION_PATHS.md)**.

---

## Troubleshooting

### Debugging Playbook

Common issues and how to debug them:

#### Issue: Suspicious Vendor Results

**Symptoms**: MAC addresses showing incorrect vendors or "Unknown" when they should be identified.

**Debugging steps**:

1. **Check OUI cache**: Inspect `output/data/oui_cache.json`
   ```bash
   grep "00:11:22" output/data/oui_cache.json
   ```

2. **Check failed lookups**: See if the OUI was previously marked as failed
   ```bash
   cat output/data/failed_lookups.json
   ```

3. **Verify MAC normalization**: Test the MAC format
   ```python
   from shadowvendor.core.shadowvendor import format_mac_address
   print(format_mac_address("your-mac-format"))
   ```

4. **Test OUI extraction**: Verify the OUI portion is correct
   ```python
   from shadowvendor.core.oui_manager import OUIManager
   oui_manager = OUIManager()
   print(oui_manager._normalize_mac("00:11:22:33:44:55"))  # Should output "00:11:22"
   ```

**Files to inspect**: `shadowvendor/core/oui_manager.py` (lines 228-302), `output/data/oui_cache.json`

#### Issue: Very Slow First Run

**Symptoms**: First run takes minutes, subsequent runs are fast.

**Root cause**: Uncached OUIs require API lookups with rate limiting.

**Solutions**:

1. **Pre-populate cache**: Run once on representative data, then use `--offline` for production
2. **Check API status**: Verify API services are responding
3. **Review rate limits**: Check if rate limits are too conservative

#### Issue: Cache Not Persisting

**Symptoms**: Vendor lookups repeated on every run despite successful API calls.

**Debugging steps**:

1. **Check file permissions**: Ensure `output/data/` is writable
2. **Check atomic write**: Review `save_cache()` in `oui_manager.py`
3. **Verify cache file**: Check if `output/data/oui_cache.json` exists and has entries
4. **Check for errors**: Look for permission errors in console output

**Files to inspect**: `shadowvendor/core/oui_manager.py` (save_cache, load_cache)

#### Issue: File Type Not Detected Correctly

**Symptoms**: MAC table treated as MAC list, or ARP table not recognized.

**Debugging steps**:

1. **Check first lines**: Inspect the first 2 lines of your input file
   ```python
   with open('your_file.txt') as f:
       print(f.readline())
       print(f.readline())
   ```

2. **Test detection functions**: Use the detection functions directly
   ```python
   from shadowvendor.core.shadowvendor import is_mac_address, is_arp_table, is_mac_address_table
   # Test with your file's first line
   ```

3. **Add debug output**: Temporarily add print statements in `ShadowVendor.py` file type detection

**Files to inspect**: `ShadowVendor.py` (file type detection), `shadowvendor/core/shadowvendor.py` (detection functions)

---

## Summary

ShadowVendor's architecture is designed for:

1. **Flexibility**: Handles multiple input formats without preprocessing
2. **Performance**: Caching and offline mode ensure fast, consistent results
3. **Reliability**: Atomic operations, error handling, and cross-platform compatibility
4. **Extensibility**: Modular design makes it easy to add new features
5. **Transparency**: Clear data flow and well-documented code

The tool transforms raw network data into actionable intelligence through a carefully orchestrated pipeline of parsing, normalization, enrichment, and output generation. Each design decision prioritizes user experience, reliability, and operational flexibility.

---

**💡 For more information:**
- See [README.md](README.md) for user documentation
- See [ADVANCED.md](ADVANCED.md) for operational best practices
- Explore the codebase: `shadowvendor/core/` and `shadowvendor/utils/`
