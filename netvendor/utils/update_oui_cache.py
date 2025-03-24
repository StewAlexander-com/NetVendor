#!/usr/bin/env python3
"""
Utility script to fetch and process the Wireshark manufacturers database.
This script downloads the Wireshark manufacturers database and converts it
into a JSON format suitable for pre-seeding the OUI cache.
"""

import os
import json
import subprocess
from typing import Dict, Set
from pathlib import Path

def fetch_wireshark_manuf() -> str:
    """
    Fetch the Wireshark manufacturers database using curl command.
    
    Returns:
        str: The raw content of the manufacturers database
    """
    # Create a temporary file to store the output
    temp_file = "manuf.txt"
    
    # Run curl command
    try:
        subprocess.run(['curl', '-L', '-o', temp_file, 'https://www.wireshark.org/download/automated/data/manuf'], 
                      check=True, capture_output=True)
        
        # Read the file content
        with open(temp_file, 'r') as f:
            content = f.read()
            
        # Clean up the temporary file
        os.remove(temp_file)
        
        return content
    except subprocess.CalledProcessError as e:
        print(f"Error fetching manufacturers database: {e}")
        raise

def parse_manuf_data(raw_data: str) -> Dict[str, str]:
    """
    Parse the raw manufacturers database into a dictionary of OUIs to vendor names.
    
    Args:
        raw_data (str): The raw content of the manufacturers database
        
    Returns:
        Dict[str, str]: Dictionary mapping OUIs to vendor names
    """
    oui_map = {}
    
    for line in raw_data.splitlines():
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Split the line into parts and get first two columns
        parts = line.strip().split('\t')
        if len(parts) < 2:
            continue
            
        oui, vendor = parts[0].strip(), parts[1].strip()
        
        # Store in the map
        oui_map[oui] = vendor
        
    return oui_map

def save_oui_cache(oui_map: Dict[str, str], output_dir: str = None) -> None:
    """
    Save the OUI map to a JSON file in the specified output directory.
    
    Args:
        oui_map (Dict[str, str]): Dictionary mapping OUIs to vendor names
        output_dir (str, optional): Directory to save the cache file. Defaults to None.
    """
    if output_dir is None:
        # Use the same directory as the OUI manager
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output', 'data')
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON file
    output_file = os.path.join(output_dir, 'oui_cache.json')
    with open(output_file, 'w') as f:
        json.dump(oui_map, f, indent=2)
    
    print(f"Saved OUI cache to {output_file}")
    print(f"Total OUIs processed: {len(oui_map)}")

def main():
    """Main function to fetch and process the Wireshark manufacturers database."""
    print("Fetching Wireshark manufacturers database...")
    raw_data = fetch_wireshark_manuf()
    
    print("Parsing manufacturers data...")
    oui_map = parse_manuf_data(raw_data)
    
    print("Saving OUI cache...")
    save_oui_cache(oui_map)

if __name__ == '__main__':
    main() 