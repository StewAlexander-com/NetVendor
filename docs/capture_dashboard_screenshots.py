#!/usr/bin/env python3
"""
Capture actual screenshots from the generated HTML dashboard.

This script takes screenshots of the actual vendor_distribution.html file
to ensure README images accurately represent what users will see.
"""

import os
import sys
from pathlib import Path

# Try to use playwright for screenshots
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available. Install with: pip install playwright && playwright install chromium")

def capture_with_playwright(html_file, output_dir):
    """Capture screenshots using Playwright."""
    html_path = Path(html_file).resolve()
    
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_file}")
        return False
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 2000})
        
        # Load the HTML file
        file_url = f"file://{html_path}"
        page.goto(file_url, wait_until='networkidle')
        
        # Wait for charts to render
        page.wait_for_timeout(2000)
        
        # Capture overview (first chart container)
        overview_path = output_dir / "overview.png"
        vendor_chart = page.locator('#vendor-distribution').first
        if vendor_chart.count() > 0:
            vendor_chart.screenshot(path=str(overview_path), type='png')
            print(f"✓ Captured overview.png")
        
        # Capture security dashboard (VLAN device count from subplot)
        security_path = output_dir / "security-dashboard.png"
        # Take screenshot of the first subplot (Total Devices per VLAN)
        first_subplot = page.locator('.js-plotly-plot').first
        if first_subplot.count() > 0:
            first_subplot.screenshot(path=str(security_path), type='png')
            print(f"✓ Captured security-dashboard.png")
        
        # Capture full vendor dashboard (all subplots)
        vendor_path = output_dir / "vendor-dashboard.png"
        vlan_chart = page.locator('#vlan-analysis').first
        if vlan_chart.count() > 0:
            vlan_chart.screenshot(path=str(vendor_path), type='png')
            print(f"✓ Captured vendor-dashboard.png")
        
        browser.close()
        return True

def main():
    """Main function to capture screenshots."""
    # Find the HTML file
    repo_root = Path(__file__).parent.parent
    html_file = repo_root / "output" / "vendor_distribution.html"
    output_dir = repo_root / "docs" / "images"
    
    if not html_file.exists():
        print(f"Error: Dashboard HTML not found at {html_file}")
        print("Please run ShadowVendor first to generate the dashboard.")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if PLAYWRIGHT_AVAILABLE:
        print("Capturing screenshots from actual dashboard...")
        if capture_with_playwright(html_file, output_dir):
            print("\n✓ All screenshots captured successfully!")
            print(f"Images saved to: {output_dir}")
        else:
            print("\n✗ Screenshot capture failed")
            sys.exit(1)
    else:
        print("Playwright not available. Using fallback method...")
        print("\nTo capture actual screenshots:")
        print("1. Install playwright: pip install playwright")
        print("2. Install browser: playwright install chromium")
        print("3. Run this script again")
        print("\nAlternatively, manually:")
        print(f"1. Open {html_file} in your browser")
        print("2. Take screenshots of the charts")
        print(f"3. Save them to {output_dir}")
        sys.exit(1)

if __name__ == "__main__":
    main()

