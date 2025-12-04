"""
SIEM Export Utilities for NetVendor

This module standardizes NetVendor results into SIEM-friendly CSV and JSONL
formats that can be ingested by systems like Elastic, Splunk, or other SIEMs.

Design goals:
- Do not change existing outputs or behavior.
- Depend only on in-memory `devices` data and the OUI manager.
- Produce simple, flat records with consistent fields.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


def _current_timestamp() -> str:
    """Return current UTC time in ISO-8601 format with 'Z' suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def export_siem_events(
    devices: Dict[str, Dict[str, str]],
    oui_manager,
    input_file: str | Path,
    site: str | None = None,
    input_type: str | None = None,
) -> None:
    """
    Export normalized events for SIEM ingestion.

    Args:
        devices: Mapping of MAC -> {'vlan': str, 'port': str}.
        oui_manager: OUIManager instance used for vendor lookups.
        input_file: Original input file path.
        site: Optional site identifier (e.g. "DC1", "HQ").
        input_type: Optional logical input type ("mac_list", "mac_table", "arp_table").

    Outputs (created in the existing `output/` directory):
        - output/netvendor_siem.csv
        - output/netvendor_siem.json
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    source_file = Path(input_file).name
    timestamp = _current_timestamp()

    csv_path = output_dir / "netvendor_siem.csv"
    json_path = output_dir / "netvendor_siem.json"

    fieldnames = [
        "timestamp",
        "site",
        "vlan",
        "port",
        "mac",
        "vendor",
        "input_type",
        "source_file",
    ]

    # Write CSV
    with csv_path.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()

        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            row = {
                "timestamp": timestamp,
                "site": site or "",
                "vlan": info.get("vlan", "N/A"),
                "port": info.get("port", "N/A"),
                "mac": mac,
                "vendor": vendor or "",
                "input_type": input_type or "",
                "source_file": source_file,
            }
            writer.writerow(row)

    # Write JSONL
    with json_path.open("w", encoding="utf-8") as f_json:
        for mac, info in devices.items():
            vendor = oui_manager.get_vendor(mac)
            event: Dict[str, Any] = {
                "timestamp": timestamp,
                "site": site,
                "vlan": info.get("vlan", "N/A"),
                "port": info.get("port", "N/A"),
                "mac": mac,
                "vendor": vendor,
                "input_type": input_type,
                "source_file": source_file,
            }
            f_json.write(json.dumps(event, ensure_ascii=False) + "\n")


