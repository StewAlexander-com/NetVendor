Features:
- Automatic format detection
- VLAN extraction from interface field
- Support for dot-separated MAC addresses

### Enhanced Format Detection
ShadowVendor now features improved file format detection:
- Automatically identifies file type based on content
- Handles multiple MAC address formats (colon-separated, dot-separated, no separators)
- Intelligently extracts VLAN information from different sources:
  * MAC tables: First column
  * ARP tables: Interface field (e.g., "Vlan10")
  * Simple MAC lists: Marked as N/A
- Preserves port information where available
- Skips header lines automatically

### Output Files
The tool generates several output files in the `output` directory:

1. **Device Information CSV**
   - Lists all discovered network devices
   - Includes MAC address, vendor, VLAN, and port information
   - Useful for inventory management and network documentation

2. **Port Report CSV** (for MAC address tables)
   - Shows port utilization on switches
   - Lists devices connected to each port
   - Includes VLAN and vendor information per port
   - Helps with network troubleshooting and capacity planning

3. **Vendor Distribution HTML**
   - Interactive dashboard with multiple visualizations
   - Vendor distribution pie chart
   - VLAN analysis charts
   - Device distribution across network segments
   - Helps network administrators understand their network composition

<img src="docs/images/vendor-dashboard.png" alt="Vendor Distribution Dashboard" width="267" style="width: 267px; height: auto;" />
*Interactive vendor distribution dashboard showing device types and network segments*

4. **Vendor Summary Text**
   - Plain text summary of vendor distribution
   - Quick reference for network documentation
   - Easy to share with team members

## Project Status
ShadowVendor is actively maintained and regularly updated with new features and improvements. Recent updates include:
- Enhanced file format detection and processing
- Improved VLAN extraction across different file types
- Better handling of various MAC address formats
- Automatic header detection and skipping

Future plans include:
- Support for additional network device output formats
- Enhanced visualization options
- Network topology mapping
- Historical data tracking
- Integration with network management systems