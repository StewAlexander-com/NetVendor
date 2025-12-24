"""
NetVendor - Network device vendor analysis tool

This package provides tools for analyzing MAC address tables, ARP tables,
and MAC lists to identify device vendors and generate distribution reports.

Main API:
    from netvendor import analyze_file
    
    result = analyze_file("mac_table.txt", offline=True)
"""

from netvendor.api import analyze_file

__all__ = ['analyze_file']

