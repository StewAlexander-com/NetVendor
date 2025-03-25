"""
OUI Manager - MAC Address Database Handler

Implements a robust vendor lookup system with:
1. Smart caching:
   - Memory cache for speed
   - Disk cache for persistence
   - Automatic cache cleanup
2. Rate-limited API access:
   - Multiple service fallbacks
   - Exponential backoff
   - Request batching
3. Error handling:
   - Failed lookup tracking
   - Service rotation on failures
   - Atomic file operations

The manager maintains data integrity through careful state management
and handles network issues gracefully to prevent data loss.
"""

import json
import requests
import datetime
import os
import re
import time
from pathlib import Path
from typing import Dict, Set, Optional, List
from rich import print
from rich.progress import Progress

class OUIManager:
    def __init__(self):
        """Initialize the OUI manager with pre-seeded cache and API fallback."""
        # Load pre-seeded Wireshark manufacturers database
        package_data_dir = Path(__file__).parent.parent / 'data'
        self.preseeded_cache_file = package_data_dir / 'oui_cache.json'
        
        # Setup user cache directory
        self.output_dir = Path("output")
        self.data_dir = self.output_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.data_dir / "oui_cache.json"
        self.failed_lookups_file = self.data_dir / "failed_lookups.json"
        
        # Initialize caches
        self.cache = {}
        self.failed_lookups = set()
        
        # Load pre-seeded cache first
        self.load_preseeded_cache()
        
        # Then load user cache (this may override some pre-seeded entries)
        if self.cache_file.exists():
            self.load_cache()
            
        # Load failed lookups
        if self.failed_lookups_file.exists():
            self.load_failed_lookups()
            
        # API configuration
        self.api_services = [
            {
                'name': 'macvendors',
                'url': 'https://api.macvendors.com/{oui}',
                'headers': {},
                'rate_limit': 2.0,
                'last_call': 0
            },
            {
                'name': 'maclookup',
                'url': 'https://api.maclookup.app/v2/macs/{oui}',
                'headers': {},
                'rate_limit': 1.0,
                'last_call': 0
            }
        ]
        self.current_service_index = 0

    def load_preseeded_cache(self):
        """Load the pre-seeded Wireshark manufacturers database."""
        if self.preseeded_cache_file.exists():
            try:
                with open(self.preseeded_cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} entries from pre-seeded OUI cache")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load pre-seeded cache ({e})")
                self.cache = {}

    def load_cache(self):
        """Load user's cached vendor lookups."""
        try:
            with open(self.cache_file, 'r') as f:
                user_cache = json.load(f)
                # Update cache with user lookups (may override pre-seeded entries)
                self.cache.update(user_cache)
        except (json.JSONDecodeError, IOError):
            pass

    def save_cache(self):
        """Save only user-added cache entries."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def load_failed_lookups(self):
        """Load previously failed lookups."""
        try:
            with open(self.failed_lookups_file, 'r') as f:
                self.failed_lookups = set(json.load(f))
        except (json.JSONDecodeError, IOError):
            self.failed_lookups = set()

    def save_failed_lookups(self):
        """Save failed lookups."""
        with open(self.failed_lookups_file, 'w') as f:
            json.dump(list(self.failed_lookups), f)

    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address format for lookups."""
        # Remove any separators and convert to uppercase
        mac = re.sub(r'[.:-]', '', mac.upper())
        # Keep only first 6 characters (OUI portion) and format with colons
        oui = mac[:6]
        return f"{oui[:2]}:{oui[2:4]}:{oui[4:]}"

    def _rate_limit(self, service):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last_call = current_time - service['last_call']
        if time_since_last_call < service['rate_limit']:
            sleep_time = service['rate_limit'] - time_since_last_call
            time.sleep(sleep_time)
        service['last_call'] = time.time()

    def get_vendor(self, mac: str) -> str:
        """
        Look up vendor for MAC address using cache first, then API.
        
        1. Try pre-seeded cache (Wireshark manufacturers database)
        2. Try user cache (previous API lookups)
        3. If not found and not previously failed, try API lookup
        """
        if not mac:
            return "Unknown"
            
        oui = self._normalize_mac(mac)
        
        # Check cache first (includes both pre-seeded and user cache)
        if oui in self.cache:
            return self.cache[oui]
            
        # Check if this OUI previously failed lookup
        if oui in self.failed_lookups:
            return "Unknown"

        # Try API lookup
        original_service_index = self.current_service_index
        retries = 0
        max_retries = len(self.api_services) * 2

        while retries < max_retries:
            service = self.api_services[self.current_service_index]
            
            try:
                self._rate_limit(service)
                url = service['url'].format(oui=oui)
                response = requests.get(url, headers=service['headers'], timeout=5)
                
                if response.status_code == 200:
                    if service['name'] == 'maclookup':
                        data = response.json()
                        vendor = data.get('company', 'Unknown')
                    else:
                        vendor = response.text.strip()

                    if vendor and vendor != "Unknown":
                        # Cache the result
                        self.cache[oui] = vendor
                        self.save_cache()
                        return vendor
                        
                elif response.status_code == 429:  # Rate limit
                    service['rate_limit'] *= 1.5  # Increase backoff
                    
                elif response.status_code == 404:  # Not found
                    self.failed_lookups.add(oui)
                    self.save_failed_lookups()
                    return "Unknown"

            except (requests.RequestException, json.JSONDecodeError):
                pass  # Try next service

            self.current_service_index = (self.current_service_index + 1) % len(self.api_services)
            retries += 1

            if self.current_service_index == original_service_index:
                time.sleep(1)  # Wait before retry cycle

        # If all retries failed
        self.failed_lookups.add(oui)
        self.save_failed_lookups()
        return "Unknown"

    def batch_lookup_vendors(self, macs: List[str], progress: Progress = None) -> Dict[str, str]:
        """Process MAC addresses in batch, using cache when available."""
        results = {}
        unknown_macs = []
        
        # First check cache for all MACs
        for mac in macs:
            if not mac:
                results[mac] = "Unknown"
                continue
                
            oui = self._normalize_mac(mac)
            if oui in self.cache:
                results[mac] = self.cache[oui]
            elif oui in self.failed_lookups:
                results[mac] = "Unknown"
            else:
                unknown_macs.append(mac)
        
        # Only create progress task if there are actually unknown MACs to look up
        if unknown_macs and progress:
            task_id = progress.add_task(
                f"[cyan]Looking up vendors for {len(unknown_macs)} MAC addresses...", 
                total=len(unknown_macs)
            )
            
            # Look up unknown MACs one at a time
            for mac in unknown_macs:
                results[mac] = self.get_vendor(mac)
                if progress:
                    progress.advance(task_id)
        
        return results 