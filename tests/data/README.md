# Test Data Directory

This directory contains generated test data for NetVendor testing.

Files:
1. test-mac-table.txt - Cisco MAC address table (500 entries)
2. test-arp-table.txt - Cisco show ip arp output (500 entries)
3. test-mac-list.txt - Simple MAC address list (100 entries)

These files are automatically generated using generate_test_files.py.
Do not modify these files manually.

The data uses real vendor OUIs and follows realistic vendor distributions:
- Cisco: ~20%
- HP: ~16%
- Dell: ~14%
- Apple: ~12%
- Juniper: ~10%
- Aruba: ~10%
- Extreme: ~8%
- Mitel: ~8%
