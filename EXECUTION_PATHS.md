# ShadowVendor Execution Paths & Behavior Graph

This document maps all ways users can run ShadowVendor, the execution flow for each path, and test coverage.

## 📊 Execution Paths Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ShadowVendor Execution Paths                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Entry Point │      │ Standalone   │      │  Python API  │
│  (Basic)     │      │ Script (Full)│      │  (Programmatic)│
│              │      │              │      │              │
│ shadowvendor    │      │ ShadowVendor.py │      │ analyze_file()│
│ -m shadowvendor │      │ [flags]      │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────────────────────────────────────────────────┐
│              Common Processing Pipeline                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ File     │→ │ Parse    │→ │ Vendor   │→ │ Generate │     │
│  │ Detection│  │ Devices  │  │ Lookup   │  │ Outputs  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                               │
│  Optional Features (if flags/config enabled):                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SIEM Export  │  │ History      │  │ Drift        │      │
│  │ (CSV/JSONL)  │  │ Archive      │  │ Analysis     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

## 🔀 Detailed Execution Paths

### Path 1: Package Entry Point (Basic)

**Command**: `shadowvendor input_file.txt` or `python3 -m shadowvendor input_file.txt`

**Flow**:
```
User Command
    │
    ▼
shadowvendor/__main__.py
    │
    ▼
shadowvendor/core/shadowvendor.py::main()
    │
    ├─> Check dependencies
    ├─> Initialize OUIManager (online mode)
    ├─> Detect file type (MAC list/ARP/MAC table)
    ├─> Parse devices
    ├─> Lookup vendors
    └─> Generate outputs:
        ├─> Device CSV
        ├─> HTML Dashboard
        └─> Vendor Summary
```

**Features**: Basic analysis only, no flags supported

**Test**: `test_package_entry_point_basic()`

---

### Path 2: Standalone Script (Full Features)

**Command**: `python3 ShadowVendor.py input_file.txt [flags]`

**Flow**:
```
User Command with Flags
    │
    ▼
ShadowVendor.py::main()
    │
    ├─> Load configuration (config file → env vars → defaults)
    ├─> Parse CLI arguments (override config)
    ├─> Initialize logger
    ├─> Initialize OUIManager (offline flag from args/config)
    │
    ├─> Detect file type
    ├─> Parse devices
    ├─> Lookup vendors
    │
    ├─> Generate standard outputs:
    │   ├─> Device CSV
    │   ├─> Port CSV (if MAC table)
    │   ├─> HTML Dashboard
    │   └─> Vendor Summary
    │
    ├─> Optional: SIEM Export (if --siem-export)
    │   └─> Generate CSV/JSONL in output/siem/
    │
    ├─> Optional: History Archive (if --history-dir)
    │   ├─> Archive vendor_summary.txt with timestamp
    │   └─> Create metadata.json
    │
    └─> Optional: Drift Analysis (if --analyze-drift)
        └─> Generate vendor_drift.csv
```

**Features**: All flags supported (--offline, --siem-export, --history-dir, --analyze-drift, etc.)

**Tests**:
- `test_standalone_script_basic()` - No flags
- `test_standalone_script_offline()` - Offline mode
- `test_standalone_script_siem_export()` - SIEM export
- `test_standalone_script_history_drift()` - History + drift
- `test_standalone_script_all_features()` - All features combined

---

### Path 3: Python API (Programmatic)

**Command**: `from shadowvendor import analyze_file`

**Flow**:
```
Python Code
    │
    ▼
shadowvendor/api.py::analyze_file()
    │
    ├─> Validate input file
    ├─> Create output directory
    ├─> Initialize logger
    ├─> Initialize OUIManager (offline parameter)
    │
    ├─> Detect file type
    ├─> Parse devices
    ├─> Enrich with vendor information
    │
    ├─> Generate standard outputs (via change_directory context)
    │   ├─> Device CSV
    │   ├─> Port CSV (if MAC table)
    │   ├─> HTML Dashboard
    │   └─> Vendor Summary
    │
    ├─> Optional: SIEM Export (if siem_export=True)
    │
    ├─> Optional: History Archive (if history_dir provided)
    │
    ├─> Optional: Drift Analysis (if analyze_drift_flag=True)
    │
    └─> Return result dictionary:
        ├─> device_count
        ├─> vendor_count
        ├─> output_files (list)
        ├─> input_type
        └─> devices (full dict)
```

**Features**: All features available via function parameters

**Tests**:
- `test_python_api_basic()` - Basic usage
- `test_python_api_all_features()` - All features

---

### Path 4: Configuration-Driven Execution

**Command**: `python3 ShadowVendor.py input_file.txt` (with config file present)

**Flow**:
```
Config File Detection
    │
    ├─> Check: ./shadowvendor.conf
    ├─> Check: ~/.config/shadowvendor/shadowvendor.conf
    └─> Check: /etc/shadowvendor/shadowvendor.conf
    │
    ▼
Load Configuration
    │
    ├─> Parse config file (INI/YAML/TOML)
    ├─> Load environment variables (SHADOWVENDOR_*)
    └─> Apply defaults
    │
    ▼
ShadowVendor.py::main()
    │
    ├─> Apply config values as defaults
    ├─> Parse CLI arguments (override config)
    └─> Continue with normal processing
```

**Precedence**: CLI args > Env vars > Config file > Defaults

**Tests**:
- `test_config_file_ini()` - Config file loading
- `test_config_file_env_override()` - Env var override
- `test_config_loading_from_file()` - Config loading
- `test_config_env_override()` - Env override

---

## 📋 Input File Type Detection

All execution paths support three input types:

```
Input File
    │
    ├─> First line is MAC address?
    │   └─> YES → MAC List
    │
    ├─> Contains "Protocol" + "Internet"?
    │   └─> YES → ARP Table
    │
    └─> Default → MAC Table
```

**Tests**:
- `test_mac_list_input()` - MAC list detection
- `test_mac_table_input()` - MAC table detection
- `test_arp_table_input()` - ARP table detection

---

## 🔄 Feature Combination Matrix

| Feature | Package Entry | Standalone Script | Python API | Config File |
|---------|--------------|-------------------|------------|-------------|
| Basic Analysis | ✅ | ✅ | ✅ | ✅ |
| Offline Mode | ❌ | ✅ | ✅ | ✅ |
| SIEM Export | ❌ | ✅ | ✅ | ✅ |
| History Archive | ❌ | ✅ | ✅ | ✅ |
| Drift Analysis | ❌ | ✅ | ✅ | ✅ |
| Port Reports | ✅ (if MAC table) | ✅ (if MAC table) | ✅ (if MAC table) | ✅ (if MAC table) |

---

## 🧪 Test Coverage Matrix

| Execution Path | Test Function | Status |
|----------------|---------------|--------|
| Package entry point (basic) | `test_package_entry_point_basic()` | ✅ |
| Module execution | `test_module_execution()` | ✅ |
| Standalone script (basic) | `test_standalone_script_basic()` | ✅ |
| Standalone script (offline) | `test_standalone_script_offline()` | ✅ |
| Standalone script (SIEM) | `test_standalone_script_siem_export()` | ✅ |
| Standalone script (drift) | `test_standalone_script_history_drift()` | ✅ |
| Standalone script (all features) | `test_standalone_script_all_features()` | ✅ |
| Python API (basic) | `test_python_api_basic()` | ✅ |
| Python API (all features) | `test_python_api_all_features()` | ✅ |
| Config file (INI) | `test_config_file_ini()` | ✅ |
| Config file (env override) | `test_config_file_env_override()` | ✅ |
| MAC list input | `test_mac_list_input()` | ✅ |
| MAC table input | `test_mac_table_input()` | ✅ |
| ARP table input | `test_arp_table_input()` | ✅ |
| Error handling (missing file) | `test_missing_input_file()` | ✅ |
| Error handling (empty file) | `test_empty_input_file()` | ✅ |
| Error handling (invalid file) | `test_invalid_input_file()` | ✅ |
| Config loading (defaults) | `test_config_loading_defaults()` | ✅ |
| Config loading (from file) | `test_config_loading_from_file()` | ✅ |
| Config loading (env override) | `test_config_env_override()` | ✅ |

**Total Test Coverage**: 20 execution paths tested

---

## 🎯 Decision Tree: Which Path to Use?

```
Do you need advanced features (offline, SIEM, drift)?
    │
    ├─> NO → Use: shadowvendor input_file.txt
    │         (Simple, fast, basic analysis)
    │
    └─> YES → Do you need programmatic control?
              │
              ├─> NO → Use: python3 ShadowVendor.py input_file.txt [flags]
              │         (Full CLI features, config file support)
              │
              └─> YES → Use: from shadowvendor import analyze_file
                        (Python API, automation-friendly)
```

---

## 📝 Notes

- **Package entry point** (`shadowvendor`) is limited to basic analysis for simplicity
- **Standalone script** (`ShadowVendor.py`) supports all features via flags
- **Python API** provides same functionality as standalone script but programmatically
- **Configuration files** reduce CLI flag churn for recurring jobs
- All paths use the same core processing pipeline for consistency

