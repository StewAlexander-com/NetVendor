"""
Drift Analysis Utilities for NetVendor

This module provides helper functions to review how vendor distributions
change over time, based on archived `vendor_summary.txt` files.

Design goals:
- Keep the existing processing pipeline untouched.
- Rely only on outputs that already exist (text summaries).
- Provide a simple, offline-friendly way to compare snapshots.

Typical workflow:
1. After each NetVendor run, copy or save the generated `vendor_summary.txt`
   with a timestamped name, e.g.:
   `cp output/vendor_summary.txt history/vendor_summary-2025-10-31.txt`
2. Point this module at the directory containing those archived summaries:
   `python -m netvendor.utils.drift_analysis history/`
3. Inspect the generated `vendor_drift.csv` for time-series changes.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Snapshot:
    """Represents a single vendor summary snapshot."""
    label: str  # e.g. filename or timestamp
    vendors: Dict[str, Tuple[int, float]]  # vendor -> (count, percentage)


def parse_vendor_summary_file(path: Path) -> Snapshot:
    """
    Parse a `vendor_summary.txt` file produced by NetVendor.

    The expected format is:
        Network Device Vendor Summary
        ...
        Vendor                         Count      Percentage
        ...
        Cisco Systems, Inc             95           19.0%

    Returns:
        Snapshot with vendor -> (count, percentage).
    """
    label = path.stem
    vendors: Dict[str, Tuple[int, float]] = {}

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    header_found = False
    for line in lines:
        line = line.rstrip("\n")
        if not header_found:
            # Look for the header row that starts the vendor table
            if line.strip().startswith("Vendor") and "Count" in line and "Percentage" in line:
                header_found = True
            continue

        # Skip separators
        if not line.strip() or set(line.strip()) <= {"-", "=", "+"}:
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        # Vendor name may contain spaces; Count and Percentage are last two fields
        try:
            count = int(parts[-2])
        except ValueError:
            continue

        perc_str = parts[-1].rstrip("%")
        try:
            percentage = float(perc_str)
        except ValueError:
            continue

        vendor_name = " ".join(parts[:-2]).strip()
        if vendor_name:
            vendors[vendor_name] = (count, percentage)

    return Snapshot(label=label, vendors=vendors)


def load_snapshots_from_directory(history_dir: Path) -> List[Snapshot]:
    """
    Load all `vendor_summary*.txt` snapshots from a directory.

    Files are sorted by name; for timestamped filenames this will generally
    correspond to chronological order.
    """
    if not history_dir.is_dir():
        raise ValueError(f"History path '{history_dir}' is not a directory")

    summary_files = sorted(history_dir.glob("vendor_summary*.txt"))
    snapshots: List[Snapshot] = []

    for path in summary_files:
        try:
            snapshots.append(parse_vendor_summary_file(path))
        except Exception:
            # Skip files that don't match the expected format
            continue

    return snapshots


def write_vendor_drift_csv(snapshots: List[Snapshot], output_path: Path) -> None:
    """
    Write a CSV summarizing vendor percentage drift over time.

    CSV structure:
        Vendor, Snapshot1, Snapshot2, ..., SnapshotN
    where each cell is the percentage of that vendor in the corresponding snapshot.
    """
    if not snapshots:
        return

    # Collect all vendor names across all snapshots
    all_vendors = set()
    for snap in snapshots:
        all_vendors.update(snap.vendors.keys())

    ordered_vendors = sorted(all_vendors)
    snapshot_labels = [s.label for s in snapshots]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["Vendor"] + snapshot_labels
        writer.writerow(header)

        for vendor in ordered_vendors:
            row = [vendor]
            for snap in snapshots:
                if vendor in snap.vendors:
                    _, pct = snap.vendors[vendor]
                    row.append(f"{pct:.1f}")
                else:
                    row.append("")
            writer.writerow(row)


def analyze_drift(history_dir: Path, output_path: Path | None = None) -> Path:
    """
    High-level helper to analyze vendor drift over time.

    Args:
        history_dir: Directory containing archived `vendor_summary*.txt` files.
        output_path: Optional path for the drift CSV. If not provided,
                     defaults to `history_dir / 'vendor_drift.csv'`.

    Returns:
        Path to the generated CSV file.
    """
    snapshots = load_snapshots_from_directory(history_dir)
    if not snapshots:
        raise RuntimeError(
            f"No vendor_summary*.txt files found in '{history_dir}'. "
            "Archive summaries from past runs before running drift analysis."
        )

    if output_path is None:
        output_path = history_dir / "vendor_drift.csv"

    write_vendor_drift_csv(snapshots, output_path)
    return output_path


def main(argv: List[str] | None = None) -> None:
    """
    Simple CLI entrypoint for drift analysis.

    Usage:
        python -m netvendor.utils.drift_analysis /path/to/history_dir
    """
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python -m netvendor.utils.drift_analysis <history_dir>")
        sys.exit(1)

    history_dir = Path(args[0])
    try:
        output_path = analyze_drift(history_dir)
    except Exception as e:
        print(f"Error analyzing drift: {e}")
        sys.exit(1)

    print(f"Vendor drift CSV written to {output_path}")


if __name__ == "__main__":
    main()


