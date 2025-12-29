# ShadowVendor Test Coverage Summary

## Overview

This document summarizes test coverage for all ShadowVendor execution paths, ensuring every way users can run the tool is validated with mock data.

## Test Suite Structure

### Execution Path Tests (`tests/test_execution_paths.py`)

**Total Tests**: 20  
**Status**: ✅ All passing

#### Package Entry Point Tests
- ✅ `test_package_entry_point_basic()` - Basic `shadowvendor input_file.txt`
- ✅ `test_module_execution()` - `python3 -m shadowvendor input_file.txt`

#### Standalone Script Tests
- ✅ `test_standalone_script_basic()` - `python3 ShadowVendor.py input_file.txt` (no flags)
- ✅ `test_standalone_script_offline()` - `--offline` flag
- ✅ `test_standalone_script_siem_export()` - `--siem-export` with site/environment
- ✅ `test_standalone_script_history_drift()` - `--history-dir --analyze-drift`
- ✅ `test_standalone_script_all_features()` - All flags combined

#### Python API Tests
- ✅ `test_python_api_basic()` - Basic `analyze_file()` usage
- ✅ `test_python_api_all_features()` - Full feature set via API

#### Configuration Tests
- ✅ `test_config_file_ini()` - INI config file loading
- ✅ `test_config_file_env_override()` - Environment variable override
- ✅ `test_config_loading_defaults()` - Default config values
- ✅ `test_config_loading_from_file()` - Config file loading
- ✅ `test_config_env_override()` - Env var precedence

#### Input Type Tests
- ✅ `test_mac_list_input()` - MAC list file detection
- ✅ `test_mac_table_input()` - MAC table file detection
- ✅ `test_arp_table_input()` - ARP table file detection

#### Error Handling Tests
- ✅ `test_missing_input_file()` - Missing file error
- ✅ `test_empty_input_file()` - Empty file error
- ✅ `test_invalid_input_file()` - Invalid/no MACs error

### Core Functionality Tests

#### `tests/test_shadowvendor.py` (9 tests)
- MAC address validation
- MAC address table detection
- Port information parsing
- Format type detection
- OUI manager cache functionality
- Failed lookups handling
- File tracking
- MAC address formatting

#### `tests/test_oui_manager.py` (8 tests - some skipped)
- Database loading
- Database saving
- Update checking
- Vendor lookups

#### `tests/test_vendor_output_handler.py` (6 tests)
- CSV generation
- Port report generation
- Vendor distribution charts
- Vendor summary saving
- Empty data handling
- Invalid data handling

#### `tests/test_api.py` (7 tests)
- MAC list analysis
- MAC table analysis
- SIEM export
- History archiving
- File not found errors
- Empty file errors
- No devices errors

## Test Data

All tests use mock data from `tests/data/`:
- `test-mac-list.txt` - Simple MAC address list
- `test-mac-table.txt` - MAC address table format
- `test-arp-table.txt` - ARP table format

Tests also create temporary files and directories to avoid polluting the workspace.

## Coverage Matrix

| Execution Path | Test Function | Mock Data | Status |
|----------------|---------------|-----------|--------|
| Package entry (basic) | `test_package_entry_point_basic()` | MAC list | ✅ |
| Module execution | `test_module_execution()` | MAC list | ✅ |
| Standalone (basic) | `test_standalone_script_basic()` | MAC table | ✅ |
| Standalone (offline) | `test_standalone_script_offline()` | MAC table | ✅ |
| Standalone (SIEM) | `test_standalone_script_siem_export()` | MAC table | ✅ |
| Standalone (drift) | `test_standalone_script_history_drift()` | MAC table | ✅ |
| Standalone (all) | `test_standalone_script_all_features()` | MAC table | ✅ |
| Python API (basic) | `test_python_api_basic()` | MAC list | ✅ |
| Python API (all) | `test_python_api_all_features()` | MAC table | ✅ |
| Config (INI) | `test_config_file_ini()` | MAC table | ✅ |
| Config (env) | `test_config_file_env_override()` | MAC table | ✅ |
| MAC list input | `test_mac_list_input()` | MAC list | ✅ |
| MAC table input | `test_mac_table_input()` | MAC table | ✅ |
| ARP table input | `test_arp_table_input()` | ARP table | ✅ |
| Error (missing) | `test_missing_input_file()` | N/A | ✅ |
| Error (empty) | `test_empty_input_file()` | Empty file | ✅ |
| Error (invalid) | `test_invalid_input_file()` | Invalid file | ✅ |
| Config defaults | `test_config_loading_defaults()` | N/A | ✅ |
| Config file | `test_config_loading_from_file()` | Config file | ✅ |
| Config env | `test_config_env_override()` | Config + env | ✅ |

## Running Tests

### Run all execution path tests:
```bash
python3 -m pytest tests/test_execution_paths.py -v
```

### Run all tests:
```bash
python3 -m pytest tests/ -v
```

### Run specific test:
```bash
python3 -m pytest tests/test_execution_paths.py::test_python_api_all_features -v
```

### Run with coverage:
```bash
python3 -m pytest tests/ --cov=shadowvendor --cov-report=html
```

## Test Validation Checklist

- [x] All execution paths tested
- [x] All input file types tested (MAC list, MAC table, ARP table)
- [x] All feature flags tested (offline, SIEM, drift, history)
- [x] Configuration file support tested
- [x] Environment variable override tested
- [x] Error handling tested (missing file, empty file, invalid file)
- [x] Python API tested
- [x] Mock data used for all tests
- [x] Tests isolated (use temporary directories)
- [x] All tests passing

## Notes

- Tests use `tempfile.TemporaryDirectory()` to avoid polluting the workspace
- Tests mock `sys.argv` to simulate command-line arguments
- Tests verify output file creation and content
- OUI manager tests use real OUI cache for vendor lookups
- Some OUI manager tests are skipped if database update is needed

