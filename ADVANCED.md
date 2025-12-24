# 🔧 NetVendor Advanced Topics

This document covers advanced topics, detailed operational guidance, and in-depth technical information for NetVendor. For basic usage and quick start, see the [README.md](README.md).

## 📑 Table of Contents

- [🔒 Posture-Change Detection & Security Monitoring](#-posture-change-detection--security-monitoring)
- [✅ Operational Best Practices](#-operational-best-practices)
- [⚙️ Runtime Considerations](#️-runtime-considerations)

---

## 🔒 Posture-Change Detection & Security Monitoring

When integrated with a SIEM (Elastic, Splunk, QRadar, etc.), NetVendor transforms from a static inventory tool into a **posture-change sensor** that enables proactive security monitoring and incident response.

### Key Capabilities

- **New Vendor Detection**: Identify when previously unseen vendors appear in your network, especially in sensitive VLANs or critical infrastructure segments.
- **Vendor Drift Analysis**: Track vendor distribution changes over time and correlate with change tickets/incidents to identify unauthorized device introductions.
- **Anomaly Detection**: Use SIEM correlation rules to alert on:
  - New vendors appearing in production VLANs
  - Vendor mix shifts coinciding with change windows
  - Unauthorized device types in restricted network segments
  - Vendor changes without corresponding change tickets

### SIEM Integration Workflow

1. **Regular Collection**: Schedule NetVendor runs (e.g., hourly/daily) with `--siem-export --site <SITE> --environment <ENV>` to generate normalized events.
2. **SIEM Ingestion**: Configure Filebeat/Elastic Agent or similar to ingest `output/siem/netvendor_siem.json` (JSONL format).
3. **Correlation Rules**: Create SIEM rules that:
   - Join current NetVendor events with historical baselines using `mac`, `vlan`, `site`
   - Alert when `vendor` field changes for a known `mac` in a sensitive `vlan`
   - Detect new `mac` addresses with previously unseen `vendor` values
   - Correlate vendor changes with `change_ticket_id` from drift analysis metadata
4. **Incident Response**: Use drift analysis metadata (`run_timestamp`, `site`, `change_ticket_id`) to:
   - Link vendor mix shifts to specific change windows
   - Support 8D/5-why root cause analysis
   - Identify unauthorized device introductions during incident investigations

### Example SIEM Queries

- **New vendor in sensitive VLAN**: Find MACs where `vlan` matches sensitive VLANs and `vendor` is not in the historical baseline for that VLAN.
- **Vendor change without change ticket**: Correlate drift analysis showing vendor percentage changes with missing `change_ticket_id` values.
- **Cross-site vendor anomalies**: Compare vendor distributions across sites using `site` field to identify inconsistent device types.

### Performance Considerations for Continuous Monitoring

- **Collection Frequency**: For real-time posture monitoring, run NetVendor every 1-4 hours depending on network change velocity.
- **Baseline Maintenance**: Archive vendor summaries with `--history-dir` and `--change-ticket` to maintain accurate baselines for comparison.
- **SIEM Storage**: Each run generates ~500 bytes per device in JSONL format. For 10,000 devices, expect ~5MB per run. Plan SIEM retention accordingly.
- **Query Performance**: Index `mac`, `vlan`, `site`, and `timestamp` fields in your SIEM for optimal correlation rule performance.

---

## ✅ Operational Best Practices

### Vendor Lookup & Caching

- **Prefer offline vendor lookups**: The OUI cache is seeded and persisted under `output/data/oui_cache.json`. Run once on representative data to warm the cache; subsequent runs avoid external requests and are faster. Use `--offline` flag for air-gapped networks or to ensure consistent results without network dependencies.
- **Avoid parallel CLI runs**: OUI API lookups are rate-limited with backoff and service rotation. For batch processing, run files sequentially to prevent throttling. If running multiple analyses, use `--offline` mode after initial cache population.
- **Cache management**: The OUI cache grows over time as new vendors are discovered. Archive `output/data/oui_cache.json` with reports for reproducibility. Failed lookups are tracked in `output/data/failed_lookups.json` to avoid repeated API calls.

### Input & Processing

- **Let the tool normalize MACs**: Inputs in colon, hyphen, dot, or mask/prefix forms are accepted; output is consistently `xx:xx:xx:xx:xx:xx`. No manual formatting required.
- **Large input handling**: Use unedited device outputs. The parser skips headers and tolerates mixed casing. Ensure `output/` is writable and on local storage for speed. Files with >100K unique MACs may be slow; consider splitting very large files into batches.
- **Port reports**: Generated only for MAC address tables (not ARP or simple lists). Ensure your input file contains port information if you need port-level analysis.

### Output Management

- **Output hygiene**: Clean `output/` between runs in CI or keep it out of version control to avoid stale artifacts. Standard outputs are overwritten by default; only history archives and SIEM exports accumulate.
- **History directory management**: When using `--history-dir`, the directory is created automatically. Regularly review and archive old snapshots to manage disk space. Each snapshot includes both the summary text file and metadata JSON for correlation.
- **SIEM export organization**: SIEM exports are written to `output/siem/` directory. For continuous monitoring, configure your SIEM agent to ingest from this directory and rotate files after ingestion. Each run generates new files that overwrite previous exports.

### Historical Drift Tracking

- **Consistent site/environment tags**: Always use `--site` and `--environment` flags for drift analysis and SIEM exports. Consistent tagging enables accurate multi-site comparisons and correlation across environments.
- **Change ticket correlation**: Use `--change-ticket` when running drift analysis during change windows. This enables correlation of vendor mix shifts with specific change tickets, supporting 8D/5-why incident analysis workflows.
- **Drift analysis frequency**: Run `--analyze-drift` regularly (e.g., after each scheduled collection) to maintain up-to-date trend analysis. The drift CSV accumulates metadata rows and vendor percentage trends across all archived runs.

### SIEM Integration

- **Stable schema usage**: SIEM exports use a stable schema with all fields present in every record. Design your SIEM correlation rules to leverage `mac`, `vlan`, `site`, `environment`, and `timestamp` fields for reliable joins and filtering.
- **Collection scheduling**: For posture-change detection, schedule regular NetVendor runs (e.g., hourly/daily) with `--siem-export --site <SITE> --environment <ENV>`. Consistent collection intervals enable accurate baseline comparisons.
- **SIEM storage planning**: Each device generates ~500 bytes in JSONL format. Plan SIEM retention based on collection frequency and device count. Index `mac`, `vlan`, `site`, and `timestamp` fields for optimal query performance.

### Troubleshooting & Debugging

- **Runtime logging**: Enable `NETVENDOR_LOG=1` for structured JSONL logging to `output/netvendor_runtime.log`. Use logs for troubleshooting performance issues, error conditions, and understanding processing flow.
- **Verbose output**: Use `NETVENDOR_VERBOSE=1` for detailed processing information during development or debugging. Verbose mode shows file type detection, per-line processing, and output file previews.
- **Error review**: Check `output/data/failed_lookups.json` periodically to identify MACs that couldn't be resolved. These may indicate new vendors or data quality issues.

### Cross-Platform Considerations

- **Windows encoding**: Set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` environment variables to prevent encoding issues with device outputs on Windows.
- **File path handling**: All paths use `pathlib.Path` for cross-platform compatibility. The tool handles `/` vs `\` automatically on Windows/Linux/Mac.
- **Atomic file operations**: Cache writes use atomic operations (write to temp file, then rename) to prevent corruption if multiple processes run simultaneously or if the process is interrupted.

### Security & Privacy

- **Sensitive data handling**: Treat MAC/ARP dumps as sensitive. Review `output/data/failed_lookups.json` and `output/data/oui_cache.json` before sharing artifacts. Consider excluding these files from shared reports.
- **Air-gapped networks**: Use `--offline` mode for air-gapped networks. Pre-populate the OUI cache on a connected system, then copy `output/data/oui_cache.json` to the air-gapped system for consistent vendor identification.

### Reproducibility

- **Dependency pinning**: Pin and install dependencies from this repo. Archive `output/data/oui_cache.json` with reports for future re-runs to ensure consistent vendor identification.
- **Version tracking**: Include NetVendor version and commit hash in your reports or SIEM metadata for reproducibility. Document the flags used for each analysis run.

---

## ⚙️ Runtime Considerations

### Performance & Scalability

- **Memory usage**: All devices are loaded into memory as a dictionary. Typical runs with thousands of MACs use minimal memory (<100MB). Very large inputs (100K+ MACs) may require 500MB-1GB RAM.
- **Processing time**: 
  - **Offline mode** (`--offline`): ~0.3-0.5 seconds per 1,000 MACs (no network latency, cache-only lookups)
  - **Online mode with cached OUIs**: ~0.5-1 second per 1,000 MACs (cache hits only)
  - **Online mode with API lookups**: ~2-5 seconds per 1,000 MACs (depends on rate limits and network latency for uncached OUIs)
  - **Visualization generation**: Additional 1-3 seconds for HTML generation (same for both modes)
- **Network dependency**: With `--offline`, there is zero network dependency. Processing speed is consistent and predictable regardless of network conditions. Online mode performance varies based on network latency and API availability.
- **Duplicate MAC handling**: Duplicate MAC addresses in input files are automatically deduplicated (last occurrence overwrites earlier ones).
- **File size limits**: No hard limits, but processing files with >100K unique MACs may be slow. Consider splitting very large files into batches. Offline mode handles large files more efficiently due to no network overhead.

### Network & API Behavior

- **Internet connectivity**: API vendor lookups require internet access only when new OUIs are encountered. With `--offline` flag, the tool operates entirely without network access, using only the local OUI cache. This makes NetVendor suitable for air-gapped networks and ensures consistent, fast results.
- **Offline mode performance**: When using `--offline`, processing is significantly faster (no network latency) and completely deterministic. All vendor lookups come from `output/data/oui_cache.json`. Uncached MACs will appear as `Unknown` in this mode.
- **Online mode behavior**: Without `--offline`, the tool will attempt API lookups for unknown OUIs. API requests have a 5-second timeout per request to prevent hangs on slow/unreliable networks. Failed requests are retried with exponential backoff across multiple services (maximum 2 retry cycles per service).
- **Rate limiting**: When online, automatic rate limiting (1-2 seconds between calls) prevents API throttling. Service rotation handles temporary failures gracefully.
- **No infinite hangs**: All network operations are bounded by timeouts. Even if all API services are unavailable, the tool will complete within a reasonable time (worst case: ~30 seconds for 100 uncached MACs with all retries). With `--offline`, there are no network operations, so execution time is purely based on processing speed.
- **Recommended workflow**: For production environments, run once with internet access to populate the cache, then use `--offline` for all subsequent runs. This eliminates network dependencies and ensures consistent, fast execution.

### Disk Space & Output Files

- **Output directory**: Requires write permissions. Creates `output/` directory if missing.
- **File sizes**: 
  - Device CSV: ~50 bytes per device
  - Port CSV (MAC tables only): ~200-500 bytes per port
  - HTML dashboard: ~30-80KB base + ~0.5KB per vendor
  - Vendor summary: ~50 bytes per vendor
  - SIEM export: ~500 bytes per device (JSONL format)
- **Multiple runs**: Output files are overwritten by default. Previous outputs are not preserved unless manually backed up.
- **History directory**: When using `NetVendor.py` with `--history-dir`, the directory is automatically created if it doesn't exist. Timestamped copies of `vendor_summary.txt` and companion `.metadata.json` files are stored there. The `vendor_drift.csv` is created when `--analyze-drift` is enabled.
- **SIEM export directory**: When using `--siem-export`, both `netvendor_siem.csv` and `netvendor_siem.json` are created in the `output/siem/` directory. Each file contains one record per device with all required fields for SIEM correlation. The `siem/` directory is automatically created if it doesn't exist.
- **Runtime log file**: When `NETVENDOR_LOG=1` is set, `output/netvendor_runtime.log` is created with structured JSONL entries for troubleshooting and performance analysis.

### Error Handling

- **Missing dependencies**: Tool exits with clear error message if required packages are missing.
- **Invalid input files**: Malformed lines are silently skipped; processing continues for valid entries.
- **API failures**: Failed vendor lookups are cached in `failed_lookups.json` to avoid repeated attempts. These appear as "Unknown" in output.
- **Write failures**: If output directory cannot be created or files cannot be written, the tool exits with an error message.
- **Cross-platform file operations**: All file writes use atomic operations (write to temp file, then rename) to prevent corruption on Windows/Linux/Mac if the process is interrupted. File encoding is explicitly set to UTF-8 to prevent encoding issues on Windows.
- **Permission errors**: Clear error messages with hints for permission issues on all platforms (Windows, Linux, macOS).

---

**💡 Tip:** For detailed usage examples and quick reference, see the [README.md](README.md).

