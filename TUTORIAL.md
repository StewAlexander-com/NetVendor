# 🔍 NetVendor Technical Tutorial

**A Deep Dive into How NetVendor Works**

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
- Integrate NetVendor into SIEM workflows with confidence

---

## Design Decisions & Tradeoffs

This table summarizes the key architectural decisions that shape NetVendor's implementation philosophy:

| Design Decision | Rationale | Tradeoff/Consideration |
|----------------|-----------|------------------------|
| **[Offline-first OUI cache](#vendor-lookup-system)** | Enables air-gapped operation, ensures consistent results, eliminates network dependencies | Initial cache population required; uncached MACs appear as "Unknown" in offline mode |
| **[Atomic file writes](#cache-persistence)** | Prevents corruption if process is interrupted (critical for Windows/cross-platform) | Slightly more complex than direct writes; requires temp file + rename pattern |
| **[JSONL runtime logging](README.md#runtime-logging)** | Structured logs enable troubleshooting and performance analysis; one JSON object per line is SIEM-friendly | Logging disabled by default to avoid performance impact; requires explicit `NETVENDOR_LOG=1` |
| **[Rate-limited API lookups](#api-lookup-with-rate-limiting)** | Respects API service limits, prevents throttling, enables service rotation | Adds latency for uncached lookups; requires careful timing management |
| **[Multi-tier vendor lookup](#lookup-strategy)** | Cache-first strategy maximizes speed and reliability; API fallback ensures coverage | Complex state management (cache, failed_lookups, service rotation); requires careful error handling |
| **[Vendor-agnostic parsing](#file-type-detection)** | Pattern matching and heuristics handle diverse network device formats without rigid requirements | May misclassify edge cases; requires robust error handling for invalid lines |
| **[Progressive enhancement](#when-to-use-different-features)** | Basic functionality works out-of-the-box; advanced features (SIEM, drift) are opt-in via flags | Two entry points (`netvendor` vs `NetVendor.py`) can be confusing; flags required for advanced features |
| **[Stable SIEM schema](#siem-export)** | All fields present in every record enables reliable correlation rules and joins | Slightly larger file size (empty fields); requires consistent field naming across versions |
| **[Cross-platform path handling](#why-it-works-this-way)** | `pathlib.Path` and explicit UTF-8 encoding ensure Windows/Linux/macOS compatibility | Must test on all platforms; some platform-specific edge cases (e.g., Windows file locking) |
| **[Dictionary-based device storage](#processing-pipeline)** | MAC addresses as keys enable automatic deduplication; last occurrence wins | No preservation of duplicate MAC order; requires normalized MAC format as keys |

**Philosophy Summary**: NetVendor prioritizes **reliability** (offline-first, atomic operations), **performance** (caching, rate limiting), and **operational safety** (error handling, cross-platform compatibility) over convenience features that could compromise production readiness.

---

## 🗺️ Quick Reference Cheat Sheet

**If you're here to...**

- **Understand parsing logic** → See [File Type Detection](#file-type-detection) and [MAC Address Normalization](#mac-address-normalization)
- **Debug vendor lookups** → See [Vendor Lookup System](#vendor-lookup-system) and [Debugging Playbook](#debugging-playbook)
- **Add a new vendor format** → See [Extension Points: Adding a New MAC-Table Vendor Format](#adding-a-new-mac-table-vendor-format)
- **Integrate with SIEM** → See [SIEM Export](#siem-export) and [README SIEM Integration](README.md#siem-friendly-export)
- **Understand offline mode** → See [Vendor Lookup System](#vendor-lookup-system) and [Why It Works This Way](#why-it-works-this-way)
- **Modify output generation** → See [Output Generation](#output-generation) and [Extension Points: Adding a New Output Type](#adding-a-new-output-type)
- **Contribute code** → See [For Contributors](#for-contributors) section below

---

## For Contributors

**If you want to contribute code, read these sections first:**

1. **[Architecture Overview](#architecture-overview)** - Understand the modular structure
2. **[Processing Pipeline](#processing-pipeline)** - See how data flows through the system
3. **[Vendor Lookup System](#vendor-lookup-system)** - Core OUI management logic
4. **[Output Generation](#output-generation)** - How outputs are created

**Then:**
- Run `pytest -q` to see existing tests
- Look at `tests/data/` for sample input files
- Review `tests/test_netvendor.py` for parsing tests
- Check `tests/test_oui_manager.py` for vendor lookup tests

**Key extension points:**
- Adding new MAC table formats: See [Extension Points](#extension-points) below
- Adding OUI API backends: See [Extension Points: Adding Another OUI API Backend](#adding-another-oui-api-backend)
- Adding output types: See [Extension Points: Adding a New Output Type](#adding-a-new-output-type)

---

## 📑 Table of Contents

- [Design Decisions & Tradeoffs](#design-decisions--tradeoffs)
- [What NetVendor Does](#what-netvendor-does)
- [Architecture Overview](#architecture-overview)
- [Processing Pipeline](#processing-pipeline)
- [Why It Works This Way](#why-it-works-this-way)
- [When to Use Different Features](#when-to-use-different-features)
- [How the Code Operates](#how-the-code-operates)
  - [File Type Detection](#file-type-detection)
  - [MAC Address Normalization](#mac-address-normalization)
  - [Vendor Lookup System](#vendor-lookup-system)
  - [Output Generation](#output-generation)
  - [Advanced Features](#advanced-features)
- [Extension Points](#extension-points)
- [Test Strategy](#test-strategy)
- [Debugging Playbook](#debugging-playbook)

---

## What NetVendor Does

NetVendor is a network analysis tool that transforms raw network device outputs (MAC address tables, ARP tables, or simple MAC lists) into structured, actionable intelligence. At its core, it:

1. **Parses** network device outputs from multiple vendors (Cisco, Juniper, HP/Aruba, Extreme, Brocade, etc.)
2. **Normalizes** MAC addresses to a consistent format (`xx:xx:xx:xx:xx:xx`)
3. **Identifies** device vendors using IEEE OUI (Organizationally Unique Identifier) lookups
4. **Extracts** network context (VLANs, ports, interfaces)
5. **Generates** multiple output formats (CSV, HTML dashboards, text summaries)
6. **Enables** advanced features like historical drift analysis and SIEM integration

### Core Data Transformation

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

## Architecture Overview

NetVendor follows a modular architecture with clear separation of concerns:

```
NetVendor.py (Main Entry Point)
    │
    ├── netvendor/core/
    │   ├── netvendor.py          # Core parsing logic
    │   └── oui_manager.py         # Vendor lookup system
    │
    └── netvendor/utils/
        ├── vendor_output_handler.py  # CSV, HTML, text generation
        ├── drift_analysis.py        # Historical analysis
        ├── siem_export.py           # SIEM event generation
        └── runtime_logger.py        # Structured logging
```

**Key Design Principles:**
- **Separation of concerns**: Parsing, lookup, and output generation are separate modules
- **Single responsibility**: Each module has one clear purpose
- **Dependency injection**: OUI manager is passed to output handlers, enabling testing and offline mode

---

## Processing Pipeline

**Data Flow Diagram:** *This diagram shows how a single input file transforms into multiple outputs through normalization, vendor enrichment, and parallel output generation.*

```
┌─────────────────┐
│  Input File     │
│  (MAC/ARP data) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ File Type        │
│ Detection        │
│ (netvendor.py)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Line-by-Line     │
│ Parsing          │
│ (netvendor.py)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MAC Address      │
│ Normalization    │
│ (format_mac)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Device Dictionary│
│ {mac: {vlan,     │
│       port}}     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vendor Lookup    │
│ (OUIManager)     │
│ Cache → API      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Enriched Devices │
│ {mac: {vlan,     │
│       port,       │
│       vendor}}   │
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┬──────────────┐
         ▼                  ▼                  ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Device CSV   │  │ HTML         │  │ Text         │  │ SIEM Export  │
│              │  │ Dashboard    │  │ Summary      │  │ (optional)   │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

**Processing Steps:**

1. **Entry Point** (`NetVendor.py`): Parses CLI arguments, initializes logger and OUI manager
2. **File Type Detection**: Reads first 2 lines to determine format (MAC list, ARP table, or MAC table)
3. **Line-by-Line Parsing**: Extracts MAC addresses, VLANs, and ports based on detected format
4. **MAC Normalization**: Converts all MAC formats to `xx:xx:xx:xx:xx:xx`
5. **Vendor Lookup**: Enriches devices with vendor information via OUI lookup
6. **Output Generation**: Creates CSV, HTML, text, and optionally SIEM exports in parallel

---

## Why It Works This Way

### Design Philosophy

NetVendor was designed with several key principles:

1. **Vendor-Agnostic Parsing**: Network devices from different manufacturers output data in different formats. NetVendor uses pattern matching and heuristics rather than rigid format requirements, making it flexible and robust.

2. **Offline-First Architecture**: The tool prioritizes local caching and can operate entirely offline. This is critical for air-gapped networks and ensures consistent, fast results.

3. **Progressive Enhancement**: Basic functionality works out-of-the-box, with advanced features (SIEM export, drift analysis) available via flags. This keeps the tool accessible while supporting enterprise use cases.

4. **Atomic Operations**: File writes use atomic patterns (write to temp file, then rename) to prevent corruption if the process is interrupted. This is especially important on Windows.

5. **Cross-Platform Compatibility**: All file operations use `pathlib.Path` and explicit UTF-8 encoding to work seamlessly on Linux, macOS, and Windows.

### Key Design Decisions

#### Why Multiple File Type Detection?

Different network teams use different data sources:
- **MAC Lists**: Simple, portable, vendor-agnostic
- **MAC Tables**: Rich context (VLANs, ports) from switches
- **ARP Tables**: Router/L3 device data with IP context

NetVendor auto-detects the format, eliminating manual preprocessing.

#### Why OUI Caching?

Vendor lookups can be slow (network latency) and rate-limited (API restrictions). By caching OUI lookups:
- **Speed**: Subsequent runs are 10-100x faster
- **Reliability**: Works offline after initial cache population
- **Cost**: Reduces API calls and respects rate limits

#### Why Multiple Output Formats?

Different stakeholders need different views:
- **CSV**: For spreadsheet analysis and automation
- **HTML Dashboard**: For interactive exploration and presentations
- **Text Summary**: For quick CLI review
- **SIEM Export**: For security monitoring integration

---

## When to Use Different Features

For detailed usage instructions and examples, see the [README.md Common Workflows section](README.md#-common-workflows). This section provides a brief technical overview of what happens internally when each feature is used.

### Basic Analysis (Default)

**Technical behavior**: Standard parsing pipeline with vendor lookups using cache-first strategy, falling back to API for uncached OUIs. See [Vendor Lookup System](#vendor-lookup-system) for details.

### Offline Mode (`--offline`)

**Technical behavior**: Sets `OUIManager(offline=True)`, which skips all API calls and uses only the local cache. Uncached MACs are added to `failed_lookups` set and appear as "Unknown". See [Vendor Lookup System: Architecture](#architecture) for implementation details.

### Historical Drift Analysis (`--history-dir --analyze-drift`)

**Technical behavior**: Archives `vendor_summary.txt` with timestamp, creates companion `.metadata.json`, then calls `analyze_drift()` to parse all archived summaries and generate `vendor_drift.csv`. See [Advanced Features: Historical Drift Analysis](#historical-drift-analysis) for implementation.

### SIEM Integration (`--siem-export`)

**Technical behavior**: Calls `export_siem_events()` which generates normalized CSV/JSONL files with stable schema. Each device becomes a SIEM event with all required fields. See [Advanced Features: SIEM Export](#siem-export) for schema details.

---

## How the Code Operates

The following sections dive deep into each component of the processing pipeline:

#### Step 1: Entry Point and Initialization

**File**: `NetVendor.py`

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

**File**: `NetVendor.py` (lines 271-296)

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

**File**: `NetVendor.py` (lines 290-335)

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
elif is_arp:
    parts = line.split(None, 5)  # Split into max 6 parts
    if len(parts) >= 6 and parts[0] == "Internet":
        mac = parts[3].strip()  # Hardware address is 4th field
        interface = parts[5].strip()  # Interface is last field
        
        mac_formatted = format_mac_address(mac)
        if mac_formatted:
            vlan = interface.replace('Vlan', '') if 'Vlan' in interface else 'N/A'
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

### File Type Detection

NetVendor uses multiple heuristics to detect file types:

#### MAC Address Validation

**File**: `netvendor/core/netvendor.py` (lines 22-71)

```python
def is_mac_address(mac: str) -> bool:
    """
    Check if a string is a valid MAC address.
    Supports formats:
    - 00:11:22:33:44:55 (standard)
    - 00-11-22-33-44-55 (standard)
    - 001122334455 (no separators)
    - 0011.2233.4455 (dot notation)
    - 00:11:22:33:44:55/ff:ff:ff:ff:ff:ff (Juniper mask)
    """
    if not mac:
        return False
    
    # Split on common separators to handle mask formats
    parts = re.split(r'[/\s]', mac.strip())
    mac_part = parts[0].lower()
    
    # Remove all separators from MAC part
    mac_clean = mac_part.replace(':', '').replace('-', '').replace('.', '')
    
    # Check length
    if len(mac_clean) != 12:
        return False
    
    # Check if all characters are valid hex
    try:
        int(mac_clean, 16)
        return True
    except ValueError:
        return False
```

**Why this approach**:
- **Flexible**: Handles all common MAC formats
- **Vendor-agnostic**: Works with Cisco dots, Juniper masks, etc.
- **Robust**: Validates hex characters, not just format

#### ARP Table Detection

**File**: `netvendor/core/netvendor.py` (lines 121-141)

```python
def is_arp_table(line: str) -> bool:
    """Check if a line is from an ARP table."""
    # Check for header
    if "Protocol" in line and "Address" in line and "Hardware Addr" in line:
        return True
    
    # Check for data line format
    parts = line.split(None, 5)  # Split into max 6 parts
    if len(parts) >= 6:
        if parts[0] != "Internet":
            return False
        
        # Check if fourth field (hardware address) is in MAC format
        mac = parts[3].strip()
        return is_arp_table_mac(mac)
    
    return False
```

**Why**: ARP tables have a specific structure (Protocol, Address, Age, Hardware Addr, Type, Interface). The function checks for both header patterns and data line structure.

#### MAC Table Detection

**File**: `netvendor/core/netvendor.py` (lines 143-194)

```python
def is_mac_address_table(line: str) -> bool:
    """Check if a line is from a MAC address table."""
    # Check for header line variations
    header_patterns = [
        ["Vlan", "Mac Address"],
        ["VLAN", "MAC Address"],
        ["VLAN ID", "MAC Address"],
        # ... more patterns
    ]
    
    if any(all(word.lower() in line.lower() for word in header) for header in header_patterns):
        return True
    
    # Check data line: VLAN number + MAC address
    words = line.strip().split()
    if len(words) < 2:
        return False
    
    # Try to extract VLAN - different vendors use different positions
    vlan = None
    for word in words[:2]:
        try:
            vlan_num = int(word)
            if 1 <= vlan_num <= 4094:  # Valid VLAN range
                vlan = vlan_num
                break
        except ValueError:
            continue
    
    if vlan is None:
        return False
    
    # Find MAC address - it's usually after VLAN
    mac_index = words.index(str(vlan)) + 1
    if mac_index >= len(words):
        return False
    
    return is_mac_address(words[mac_index])
```

**Why**: MAC tables vary significantly between vendors. The function uses multiple header patterns and validates that the line contains a valid VLAN (1-4094) followed by a valid MAC address.

### MAC Address Normalization

**File**: `netvendor/core/netvendor.py` (lines 94-119)

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
| `D8.C7.C8.14C17B` | `d8:c7:c8:14:c1:7b` |

**Why normalization**:
- **Consistency**: All MACs in output use same format
- **Deduplication**: Same device with different input formats becomes one entry
- **Lookup efficiency**: OUI cache uses normalized format as keys

### Vendor Lookup System

The `OUIManager` class is the heart of vendor identification. Let's explore how it works:

#### Architecture

**File**: `netvendor/core/oui_manager.py`

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

#### Lookup Strategy

The vendor lookup follows a multi-tier strategy:

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

**Code Flow**:

```python
def get_vendor(self, mac: str) -> str:
    """Look up vendor for MAC address using cache first, then API."""
    if not mac:
        return None

    oui = self._normalize_mac(mac)  # Extract first 6 hex chars (OUI)
    
    # Check failed lookups first (don't retry)
    if oui in self.failed_lookups:
        return None
    
    # Check cache
    if oui in self.cache:
        return self.cache[oui]

    # In offline mode, never attempt external lookups
    if self.offline:
        self.failed_lookups.add(oui)
        self.save_failed_lookups()
        return None

    # Try API lookup with service rotation and retries
    # ... (see API lookup section below)
```

#### OUI Normalization

**File**: `netvendor/core/oui_manager.py` (lines 211-217)

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

**File**: `netvendor/core/oui_manager.py` (lines 256-302)

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
        response = requests.get(url, headers=service['headers'], timeout=5)
        
        if response.status_code == 200:
            # Parse response based on service
            if service['name'] == 'maclookup':
                data = response.json()
                vendor = data.get('company', 'Unknown')
            else:
                vendor = response.text.strip()
            
            if vendor and vendor != "Unknown":
                # Cache the result
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
    self.current_service_index = (self.current_service_index + 1) % len(self.api_services)
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

#### Rate Limiting Implementation

**File**: `netvendor/core/oui_manager.py` (lines 219-226)

```python
def _rate_limit(self, service):
    """Implement rate limiting for API calls."""
    current_time = time.time()
    time_since_last_call = current_time - service['last_call']
    if time_since_last_call < service['rate_limit']:
        sleep_time = service['rate_limit'] - time_since_last_call
        time.sleep(sleep_time)
    service['last_call'] = time.time()
```

**Why**: Different API services have different rate limits. The manager tracks the last call time per service and enforces delays accordingly.

#### Cache Persistence

**File**: `netvendor/core/oui_manager.py` (lines 157-178)

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

### Output Generation

NetVendor generates multiple output formats, each serving different use cases:

#### Device CSV Generation

**File**: `netvendor/utils/vendor_output_handler.py` (lines 26-67)

```python
def make_csv(input_file: Union[Path, str], devices: Dict[str, Dict[str, str]], oui_manager: OUIManager) -> None:
    """Creates a CSV file with device information."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    if isinstance(input_file, str):
        input_file = Path(input_file)
    
    output_file = output_dir / f"{input_file.stem}-Devices.csv"
    
    with Progress(...) as progress:
        task = progress.add_task("[cyan]Writing device information...", total=len(devices))
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['MAC', 'Vendor', 'VLAN', 'Port'])
            
            for mac, info in devices.items():
                vendor = oui_manager.get_vendor(mac)
                vendor = vendor if vendor is not None else "Unknown"
                vlan = info.get('vlan', 'N/A')
                port = info.get('port', 'N/A')
                writer.writerow([mac, vendor, vlan, port])
                progress.advance(task)
```

**Why**:
- **Progress bar**: Shows user that processing is happening (important for large files)
- **UTF-8 encoding**: Ensures special characters work on all platforms
- **None handling**: Converts None vendors to "Unknown" (happens in offline mode)

#### HTML Dashboard Generation

**File**: `netvendor/utils/vendor_output_handler.py` (lines 134-391)

The HTML dashboard uses Plotly to create interactive visualizations:

```python
def create_vendor_distribution(devices: Dict[str, Dict[str, str]], oui_manager, input_file: Path) -> None:
    """Creates interactive visualizations of vendor and VLAN distributions."""
    
    # Collect vendor data
    vendor_counts = Counter()
    for mac, info in devices.items():
        vendor = oui_manager.get_vendor(mac)
        vendor = vendor if vendor is not None else "Unknown"
        vendor_counts[vendor] += 1
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Vendor Distribution', 'VLAN Device Count', ...),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "heatmap"}]]
    )
    
    # Add pie chart
    fig.add_trace(
        go.Pie(labels=list(vendor_counts.keys()), 
               values=list(vendor_counts.values()),
               hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>'),
        row=1, col=1
    )
    
    # ... more charts ...
    
    # Save as HTML
    fig.write_html('output/vendor_distribution.html')
```

**Why Plotly**:
- **Interactive**: Users can hover, zoom, filter
- **Self-contained**: HTML file includes all JavaScript, no external dependencies
- **Professional**: Publication-quality visualizations

#### Port Report Generation

**File**: `netvendor/utils/vendor_output_handler.py` (lines 69-132)

```python
def generate_port_report(input_file: str, devices: Dict[str, Dict[str, str]], oui_manager, is_mac_table: bool = True) -> None:
    """Generate a CSV report analyzing devices connected to each network port."""
    
    # Group devices by port
    port_data = {}
    for mac, device in devices.items():
        port = device.get('port', '')
        if port not in port_data:
            port_data[port] = {
                'total_devices': 0,
                'vlans': set(),
                'vendors': set(),
                'devices': []
            }
        
        port_info = port_data[port]
        port_info['total_devices'] += 1
        port_info['vlans'].add(device.get('vlan', ''))
        vendor = oui_manager.get_vendor(mac)
        vendor = vendor if vendor is not None else "Unknown"
        port_info['vendors'].add(vendor)
        port_info['devices'].append(mac)
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Port', 'Total Devices', 'VLANs', 'Vendors', 'Devices'])
        for port, info in port_data.items():
            writer.writerow([
                port,
                info['total_devices'],
                ','.join(sorted(info['vlans'])),
                ','.join(sorted(info['vendors'])),
                ','.join(info['devices'])
            ])
```

**Why**: Port reports help network engineers understand:
- Which ports have the most devices (potential issues)
- VLAN distribution per port
- Vendor diversity per port

### Advanced Features

#### Historical Drift Analysis

**File**: `netvendor/utils/drift_analysis.py`

Drift analysis tracks how vendor distributions change over time:

```python
def analyze_drift(history_dir: Path, site: str = None, change_ticket_id: str = None) -> None:
    """
    Analyze vendor distribution changes across archived summaries.
    
    Creates vendor_drift.csv with:
    - Metadata rows (run_timestamp, site, change_ticket_id)
    - Vendor percentage rows showing changes over time
    """
    # Find all vendor summary files
    summary_files = sorted(history_dir.glob("vendor_summary-*.txt"))
    
    snapshots = []
    for summary_file in summary_files:
        snapshot = parse_vendor_summary_file(summary_file)
        # Load companion metadata if exists
        metadata_file = summary_file.with_suffix('.metadata.json')
        if metadata_file.exists():
            with metadata_file.open('r') as f:
                metadata = json.load(f)
                snapshot.run_timestamp = metadata.get('run_timestamp')
                snapshot.site = metadata.get('site')
                snapshot.change_ticket_id = metadata.get('change_ticket_id')
        snapshots.append(snapshot)
    
    # Generate drift CSV
    # ... (calculates percentage changes)
```

**Use Case**: Track vendor mix changes and correlate with change tickets for incident analysis.

#### SIEM Export

**File**: `netvendor/utils/siem_export.py`

SIEM export creates normalized events for security monitoring:

```python
def export_siem_events(
    devices: Dict[str, Dict[str, str]],
    oui_manager,
    input_file: str | Path,
    site: str | None = None,
    environment: str | None = None,
    input_type: str | None = None,
) -> None:
    """Export normalized events for SIEM ingestion with stable schema."""
    
    timestamp = _current_timestamp()  # UTC ISO-8601
    source_file = Path(input_file).name
    
    # Write CSV and JSONL
    with csv_path.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            vendor = vendor if vendor is not None else "Unknown"
            
            record = {
                "timestamp": timestamp,
                "site": site or "",
                "environment": environment or "",
                "mac": mac,
                "vendor": vendor,
                "device_name": f"device_{mac.replace(':', '')}",
                "vlan": info.get('vlan', 'N/A'),
                "interface": info.get('port', 'N/A'),
                "input_type": input_type or "unknown",
                "source_file": source_file,
            }
            writer.writerow(record)
```

**Why stable schema**: SIEM correlation rules depend on consistent field names and presence. Every record has all fields, even if empty.

---

## Extension Points

This section provides step-by-step guides for extending NetVendor's functionality.

### Adding a New MAC-Table Vendor Format

**When**: You encounter a switch vendor whose MAC table format isn't recognized.

**Steps**:

1. **Add header pattern** in `netvendor/core/netvendor.py`, function `is_mac_address_table()`:
   ```python
   header_patterns = [
       # ... existing patterns ...
       ["VLAN", "MAC", "Type", "YourVendorHeader"],  # Add your pattern
   ]
   ```

2. **Test detection** by adding a test case in `tests/test_netvendor.py`:
   ```python
   def test_your_vendor_format():
       assert is_mac_address_table("VLAN MAC Type YourVendorHeader")
   ```

3. **Verify parsing** - The existing parsing logic in `NetVendor.py` (lines 320-335) should handle most formats, but if your vendor uses a different column order, modify the parsing logic there.

4. **Run tests**: `pytest tests/test_netvendor.py::test_your_vendor_format -v`

**Files to modify**: `netvendor/core/netvendor.py`, `tests/test_netvendor.py`

### Adding Another OUI API Backend

**When**: You want to add a fallback API service or replace an existing one.

**Steps**:

1. **Add service configuration** in `netvendor/core/oui_manager.py`, `__init__()` method:
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

**Files to modify**: `netvendor/core/oui_manager.py`

### Adding a New Output Type

**When**: You want to generate a different output format (e.g., JSON, XML, database export).

**Steps**:

1. **Create new function** in `netvendor/utils/vendor_output_handler.py`:
   ```python
   def generate_your_format(devices: Dict, oui_manager: OUIManager, input_file: Path) -> None:
       """Generate your custom output format."""
       output_file = Path("output") / f"{input_file.stem}.yourformat"
       # Your generation logic here
   ```

2. **Call from main script** in `NetVendor.py`, after other output generation:
   ```python
   from netvendor.utils.vendor_output_handler import generate_your_format
   # ... existing outputs ...
   generate_your_format(devices, oui_manager, input_file)
   ```

3. **Add tests** in `tests/test_vendor_output_handler.py`:
   ```python
   def test_generate_your_format(temp_output_dir, sample_device_data, monkeypatch):
       # Test your format generation
   ```

**Files to modify**: `netvendor/utils/vendor_output_handler.py`, `NetVendor.py`, `tests/test_vendor_output_handler.py`

---

## Test Strategy

NetVendor's test suite is located in `tests/` and provides comprehensive coverage of all execution paths, core functionality, and edge cases. This section explains **how the testing process works**, from running tests to understanding results.

### Understanding the Test Process

**What happens when you run tests:**

1. **Test Discovery**: pytest automatically finds all test files (files starting with `test_`) and test functions (functions starting with `test_`)
2. **Fixture Setup**: Before each test, pytest runs fixtures (like `temp_dir`, `sample_mac_table_file`) to set up test data
3. **Test Execution**: Each test function runs in isolation with its own temporary directory
4. **Assertion Validation**: Tests use `assert` statements to verify expected behavior
5. **Cleanup**: Temporary files and directories are automatically cleaned up after each test

**Test isolation**: Each test runs in its own temporary directory (`tempfile.TemporaryDirectory()`), so tests don't interfere with each other or pollute your workspace.

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                      # Shared fixtures (temp_dir, sample files)
├── test_execution_paths.py         # All execution paths (20+ tests)
├── test_netvendor.py                # Parsing and format detection tests
├── test_oui_manager.py              # Vendor lookup and caching tests
├── test_vendor_output_handler.py    # Output generation tests
├── test_api.py                      # Python API tests
└── data/                            # Sample input files
    ├── test-mac-list.txt            # 100 MAC addresses
    ├── test-mac-table.txt            # 500+ MAC table entries
    └── test-arp-table.txt           # ARP table format
```

**Key components:**

- **`conftest.py`**: Defines shared fixtures (test data setup) used across all test files
- **`test_*.py`**: Individual test files organized by functionality
- **`data/`**: Mock input files representing real-world network device outputs
- **Fixtures**: Reusable test data (e.g., `temp_dir` creates temporary directories, `sample_mac_table_file` creates test input files)

### Execution Path Testing

**Comprehensive execution path validation** (`test_execution_paths.py` - 20 tests):

NetVendor validates every way users can run the tool:

1. **Package Entry Point** (2 tests):
   - `test_package_entry_point_basic()` - `netvendor input_file.txt`
   - `test_module_execution()` - `python3 -m netvendor input_file.txt`

2. **Standalone Script** (5 tests):
   - `test_standalone_script_basic()` - No flags
   - `test_standalone_script_offline()` - Offline mode
   - `test_standalone_script_siem_export()` - SIEM export
   - `test_standalone_script_history_drift()` - History + drift analysis
   - `test_standalone_script_all_features()` - All features combined

3. **Python API** (2 tests):
   - `test_python_api_basic()` - Basic `analyze_file()` usage
   - `test_python_api_all_features()` - Full feature set

4. **Configuration** (5 tests):
   - Config file loading (INI, YAML, TOML)
   - Environment variable overrides
   - Configuration precedence validation

5. **Input Types** (3 tests):
   - MAC list detection and parsing
   - MAC table detection and parsing
   - ARP table detection and parsing

6. **Error Handling** (3 tests):
   - Missing file errors
   - Empty file errors
   - Invalid input errors

**Why this matters**: These tests ensure that whether users run NetVendor via CLI, Python API, or configuration files, all paths work correctly and produce expected outputs.

See **[EXECUTION_PATHS.md](EXECUTION_PATHS.md)** for detailed execution path documentation and behavior graphs.

### Core Functionality Testing

**Parsing Functions** (`test_netvendor.py`):
- `test_is_mac_address()` - Validates MAC address detection across formats (colon, hyphen, dot, mask formats)
- `test_is_mac_address_table()` - Tests MAC table format detection (Cisco, HP/Aruba, Juniper, Extreme, Brocade)
- `test_format_mac_address()` - Ensures normalization works correctly (all formats → `xx:xx:xx:xx:xx:xx`)
- `test_parse_port_info()` - Port extraction from various formats

**Vendor Lookup** (`test_oui_manager.py`):
- `test_oui_manager_cache()` - Verifies caching behavior with real OUIs
- `test_oui_manager_failed_lookups()` - Tests failure handling and tracking
- `test_get_vendor_ouis()` - Validates OUI extraction and normalization

**Output Generation** (`test_vendor_output_handler.py`):
- `test_make_csv()` - CSV generation with various data scenarios
- `test_generate_port_report()` - Port report creation and formatting
- `test_create_vendor_distribution()` - HTML dashboard generation
- `test_save_vendor_summary()` - Vendor summary text file creation
- `test_empty_data_handling()` - Edge case handling

**Python API** (`test_api.py`):
- API function signatures and return values
- Error handling and validation
- Feature flag combinations

### Running Tests

**Basic test execution:**

```bash
# Run all tests (quick summary)
pytest -q
# Output: Shows pass/fail count, e.g., "20 passed in 2.34s"

# Run all tests (verbose - shows each test name)
pytest -v
# Output: Lists each test with PASSED/FAILED status

# Run execution path tests (comprehensive validation)
pytest tests/test_execution_paths.py -v

# Run specific test file
pytest tests/test_netvendor.py -v

# Run specific test function
pytest tests/test_netvendor.py::test_is_mac_address -v

# Run with coverage report (shows which code is tested)
pytest --cov=netvendor --cov-report=html
# Opens htmlcov/index.html in browser showing line-by-line coverage
```

**Understanding test output:**

- **PASSED**: Test completed successfully, all assertions passed
- **FAILED**: An assertion failed or an exception occurred
- **SKIPPED**: Test was skipped (e.g., missing optional dependency)
- **ERROR**: Test setup/fixture failed before test could run

**Example test run output:**
```
tests/test_execution_paths.py::test_package_entry_point_basic PASSED     [  5%]
tests/test_execution_paths.py::test_module_execution PASSED              [ 10%]
tests/test_execution_paths.py::test_standalone_script_basic PASSED       [ 15%]
...
============================= 20 passed in 22.42s ==============================
```

### How Tests Work: Step-by-Step Example

Let's walk through what happens when a test runs:

**Example: `test_standalone_script_basic()`**

```python
def test_standalone_script_basic(sample_mac_table_file, temp_dir):
    """Test: python3 NetVendor.py input_file.txt (basic, no flags)."""
    from NetVendor import main
    import sys
    
    with patch('sys.argv', ['NetVendor.py', str(sample_mac_table_file)]):
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            main()
            
            # Verify standard outputs
            assert (temp_dir / "output" / f"{sample_mac_table_file.stem}-Devices.csv").exists()
            assert (temp_dir / "output" / "vendor_distribution.html").exists()
        finally:
            os.chdir(old_cwd)
```

**Test execution flow:**

1. **Fixture execution**: pytest calls `sample_mac_table_file(temp_dir)` and `temp_dir()` fixtures
   - `temp_dir()` creates a temporary directory (e.g., `/tmp/tmpXYZ123`)
   - `sample_mac_table_file()` creates a test MAC table file in that directory

2. **Test setup**: 
   - `patch('sys.argv', ...)` mocks command-line arguments
   - `os.chdir(temp_dir)` changes to the temporary directory

3. **Test execution**:
   - `main()` runs NetVendor with the mocked arguments
   - NetVendor processes the test file and generates outputs

4. **Assertion validation**:
   - `assert (temp_dir / "output" / "...-Devices.csv").exists()` checks if CSV was created
   - `assert (temp_dir / "output" / "vendor_distribution.html").exists()` checks if HTML was created
   - If any assertion fails, the test fails

5. **Cleanup**:
   - `finally` block restores original working directory
   - Temporary directory is automatically deleted when test completes

**Why this approach works:**
- **Isolation**: Each test has its own temporary directory, so tests don't interfere
- **Reproducibility**: Tests use controlled mock data, so results are consistent
- **Validation**: Assertions verify both that code runs AND produces expected outputs
- **Cleanup**: Automatic cleanup ensures no leftover files from test runs

### Test Data

**Mock data files** in `tests/data/` represent real-world network device formats:
- `test-mac-table.txt` - Cisco-style MAC address table (500+ entries)
- `test-arp-table.txt` - Standard ARP table format
- `test-mac-list.txt` - Simple MAC address list (100 MACs)

**How test data is used:**

1. **Static test data**: Files in `tests/data/` are read-only reference files
2. **Dynamic test data**: Tests create temporary files using fixtures (e.g., `sample_mac_table_file`)
3. **Isolation**: Each test creates its own copy of test data in a temporary directory

**Adding new test data:**

1. Add a new file to `tests/data/` (e.g., `test-juniper-mac-table.txt`)
2. Create a fixture in `conftest.py` or the test file:
   ```python
   @pytest.fixture
   def sample_juniper_file(temp_dir):
       """Create a sample Juniper MAC table file."""
       test_file = temp_dir / "test_juniper.txt"
       test_file.write_text("... Juniper format content ...")
       return test_file
   ```
3. Use the fixture in your test:
   ```python
   def test_juniper_format(sample_juniper_file, temp_dir):
       result = analyze_file(sample_juniper_file, offline=True)
       assert result['device_count'] > 0
   ```

**Why temporary directories?**
- Tests don't pollute your workspace with output files
- Multiple tests can run in parallel without conflicts
- Automatic cleanup ensures no leftover files
- Each test starts with a clean slate

### Testing Philosophy

NetVendor's testing approach ensures:
- **Complete coverage**: Every execution path is validated
- **Real-world scenarios**: Tests use realistic network device outputs
- **Isolation**: Tests use temporary directories and mock data
- **Reproducibility**: All tests use controlled mock data
- **Cross-platform**: Tests validate Windows/Linux/macOS compatibility

### Writing New Tests

**Step-by-step guide for adding a new test:**

1. **Identify what to test**: Decide what functionality needs validation
   - New parser format? → Add to `test_netvendor.py`
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
       from NetVendor import main
       
       # Execute
       with patch('sys.argv', ['NetVendor.py', str(my_test_file)]):
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

### Test Validation Checklist

**Current test coverage:**
- ✅ All execution paths tested (package entry, standalone, Python API)
- ✅ All input file types tested (MAC list, MAC table, ARP table)
- ✅ All feature flags tested (offline, SIEM, drift, history)
- ✅ Configuration file support tested
- ✅ Environment variable override tested
- ✅ Error handling tested (missing file, empty file, invalid file)
- ✅ Mock data used for all tests
- ✅ Tests isolated (use temporary directories)
- ✅ All tests passing (20+ execution path tests + core functionality tests)

**How to verify test coverage:**

```bash
# Run all tests and see summary
pytest -q

# Run with coverage report
pytest --cov=netvendor --cov-report=term-missing
# Shows which lines of code are not covered by tests

# Generate HTML coverage report
pytest --cov=netvendor --cov-report=html
# Opens htmlcov/index.html showing line-by-line coverage
```

For detailed test coverage information, see **[TEST_COVERAGE.md](TEST_COVERAGE.md)** and **[EXECUTION_PATHS.md](EXECUTION_PATHS.md)**.

---

## Debugging Playbook

Common issues and how to debug them using the knowledge from this tutorial.

### Issue: Suspicious Vendor Results

**Symptoms**: MAC addresses showing incorrect vendors or "Unknown" when they should be identified.

**Debugging steps**:

1. **Check OUI cache**: Inspect `output/data/oui_cache.json` to see if the OUI is cached
   ```bash
   grep "00:11:22" output/data/oui_cache.json
   ```

2. **Check failed lookups**: See if the OUI was previously marked as failed
   ```bash
   cat output/data/failed_lookups.json
   ```

3. **Verify MAC normalization**: Test the MAC format
   ```python
   from netvendor.core.netvendor import format_mac_address
   print(format_mac_address("your-mac-format"))
   ```

4. **Test OUI extraction**: Verify the OUI portion is correct
   ```python
   from netvendor.core.oui_manager import OUIManager
   oui_manager = OUIManager()
   print(oui_manager._normalize_mac("00:11:22:33:44:55"))  # Should output "00:11:22"
   ```

5. **Enable verbose mode**: Run with `NETVENDOR_VERBOSE=1` to see lookup details

**Files to inspect**: `netvendor/core/oui_manager.py` (lines 228-302), `output/data/oui_cache.json`

### Issue: Very Slow First Run

**Symptoms**: First run takes minutes, subsequent runs are fast.

**Root cause**: Uncached OUIs require API lookups with rate limiting.

**Solutions**:

1. **Pre-populate cache**: Run once on representative data, then use `--offline` for production
2. **Check API status**: Verify API services are responding (see `netvendor/core/oui_manager.py` lines 68-83)
3. **Review rate limits**: Check if rate limits are too conservative (lines 219-226)

**Files to inspect**: `netvendor/core/oui_manager.py` (rate limiting logic)

### Issue: No SIEM Outputs Created

**Symptoms**: `--siem-export` flag used but `output/siem/` directory is empty or missing.

**Debugging steps**:

1. **Check flag parsing**: Verify `args.siem_export` is True in `NetVendor.py`
2. **Check directory creation**: Look for errors in `netvendor/utils/siem_export.py` (lines 63-72)
3. **Check permissions**: Ensure write access to `output/siem/` directory
4. **Enable runtime logging**: Run with `NETVENDOR_LOG=1` and check `output/netvendor_runtime.log`

**Files to inspect**: `NetVendor.py` (SIEM export call), `netvendor/utils/siem_export.py` (lines 27-141)

### Issue: File Type Not Detected Correctly

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
   from netvendor.core.netvendor import is_mac_address, is_arp_table, is_mac_address_table
   # Test with your file's first line
   ```

3. **Add debug output**: Temporarily add print statements in `NetVendor.py` file type detection (lines 271-296)

**Files to inspect**: `NetVendor.py` (file type detection), `netvendor/core/netvendor.py` (detection functions)

### Issue: Port Information Missing

**Symptoms**: Port column shows "N/A" for MAC table inputs.

**Debugging steps**:

1. **Verify input format**: Check if your MAC table includes port information
2. **Test port parsing**: Use `parse_port_info()` function
   ```python
   from netvendor.core.netvendor import parse_port_info
   print(parse_port_info("your-mac-table-line"))
   ```

3. **Check parsing logic**: Review MAC table parsing in `NetVendor.py` (lines 320-335)

**Files to inspect**: `NetVendor.py` (MAC table parsing), `netvendor/core/netvendor.py` (parse_port_info)

### Issue: Cache Not Persisting

**Symptoms**: Vendor lookups repeated on every run despite successful API calls.

**Debugging steps**:

1. **Check file permissions**: Ensure `output/data/` is writable
2. **Check atomic write**: Review `save_cache()` in `oui_manager.py` (lines 157-178)
3. **Verify cache file**: Check if `output/data/oui_cache.json` exists and has entries
4. **Check for errors**: Look for permission errors in console output

**Files to inspect**: `netvendor/core/oui_manager.py` (save_cache, load_cache)

---

## Summary

NetVendor's architecture is designed for:

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
- Explore the codebase: `netvendor/core/` and `netvendor/utils/`

