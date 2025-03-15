import json
import requests
import datetime
import os
from pathlib import Path
from typing import Dict, Set
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn, DownloadColumn

class OUIManager:
    def __init__(self):
        # Create output/data directory if it doesn't exist
        self.output_dir = Path("output")
        self.data_dir = self.output_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.oui_file = self.data_dir / "oui_database.json"
        self.vendors = {
            "HP": ["Hewlett Packard", "HP Enterprise", "HP Inc"],
            "Apple": ["Apple, Inc"],
            "Dell": ["Dell Inc", "Dell Technologies"],
            "Cisco": ["Cisco Systems", "Cisco SPVTG"],
            "Mitel": ["Mitel Networks"],
        }

    def load_database(self) -> Dict:
        """Load the OUI database if it exists, otherwise create a new one"""
        if self.oui_file.exists():
            with open(self.oui_file, 'r') as f:
                return json.load(f)
        return {
            "last_updated": "",
            "vendors": {vendor: [] for vendor in self.vendors}
        }

    def save_database(self, data: Dict):
        """Save the OUI database to file"""
        with open(self.oui_file, 'w') as f:
            json.dump(data, f, indent=4)

    def update_database(self) -> bool:
        """Update the OUI database from IEEE"""
        print("\n[yellow]Updating OUI database from IEEE...[/yellow]")
        
        try:
            # Create progress for download
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                # Download task
                download_task = progress.add_task("[cyan]Downloading IEEE OUI database...", total=None)
                
                # Download the IEEE OUI database
                url = "http://standards-oui.ieee.org/oui/oui.txt"
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # Mark download as complete
                progress.update(download_task, completed=True)
                
                # Process vendors task
                database = self.load_database()
                content = response.text.split('\n')
                
                # Create a new progress bar for processing vendors
                vendor_task = progress.add_task(
                    "[cyan]Processing vendor OUIs...", 
                    total=len(self.vendors)
                )
                
                # Store statistics for reporting
                stats = {}
                
                # Process each vendor
                for vendor_key, search_names in self.vendors.items():
                    progress.update(vendor_task, description=f"[cyan]Processing {vendor_key} OUIs...")
                    new_ouis = set()
                    
                    # Create a progress bar for lines processing
                    lines_task = progress.add_task(
                        f"[blue]Scanning for {vendor_key}...",
                        total=len(content)
                    )
                    
                    # Search for each vendor name variant
                    for line_num, line in enumerate(content):
                        if any(name.upper() in line.upper() for name in search_names):
                            if '(hex)' in line:
                                oui = line.split('(hex)')[0].strip().replace('-', '').lower()
                                oui = f"{oui[:4]}.{oui[4:]}"
                                new_ouis.add(oui)
                        progress.update(lines_task, completed=line_num + 1)
                    
                    # Update database with new OUIs
                    existing_ouis = set(database["vendors"].get(vendor_key, []))
                    updated_ouis = sorted(existing_ouis.union(new_ouis))
                    
                    # Store statistics
                    stats[vendor_key] = {
                        "existing": len(existing_ouis),
                        "new": len(new_ouis - existing_ouis),
                        "total": len(updated_ouis)
                    }
                    
                    database["vendors"][vendor_key] = updated_ouis
                    
                    # Complete the vendor task step
                    progress.update(vendor_task, advance=1)
                    
                    # Remove the lines task as we're done with it
                    progress.remove_task(lines_task)
                
                # Update timestamp
                database["last_updated"] = datetime.datetime.now().isoformat()
                
                # Add saving task
                save_task = progress.add_task("[cyan]Saving updated database...", total=None)
                self.save_database(database)
                progress.update(save_task, completed=True)
            
            # Print summary of updates
            print("\n[green]OUI database update completed successfully![/green]")
            print("\n[yellow]Update Summary:[/yellow]")
            for vendor, stat in stats.items():
                print(f"[cyan]{vendor}:[/cyan]")
                print(f"  • Previous OUIs: {stat['existing']}")
                print(f"  • New OUIs found: {stat['new']}")
                print(f"  • Total OUIs: {stat['total']}")
                if stat['new'] > 0:
                    print(f"  • [green]Added {stat['new']} new OUIs![/green]")
                print()
            
            return True
            
        except Exception as e:
            print(f"\n[red]Error updating OUI database: {e}[/red]")
            return False

    def check_update_needed(self) -> bool:
        """Ask user if they want to update the database"""
        database = self.load_database()
        last_updated = database.get("last_updated", "Never")
        
        if last_updated != "Never":
            try:
                last_update = datetime.datetime.fromisoformat(last_updated)
                last_update_str = last_update.strftime("%Y-%m-%d %H:%M:%S")
                
                # Calculate days since last update
                days_since_update = (datetime.datetime.now() - last_update).days
                if days_since_update > 30:
                    print(f"\n[yellow]Warning: OUI database is over {days_since_update} days old[/yellow]")
            except:
                last_update_str = last_updated
        else:
            last_update_str = "Never"
            print("\n[yellow]Warning: OUI database has never been updated[/yellow]")

        print(f"\n[yellow]OUI database was last updated: [cyan]{last_update_str}[/cyan][/yellow]")
        
        # Show current OUI counts
        print("\n[yellow]Current OUI database status:[/yellow]")
        for vendor in self.vendors:
            oui_count = len(database["vendors"].get(vendor, []))
            print(f"[cyan]{vendor}:[/cyan] {oui_count} OUIs")
        
        response = input("\nWould you like to update the OUI database? (y/N): ").lower()
        return response == 'y'

    def get_vendor_ouis(self, vendor: str) -> Set[str]:
        """Get the OUIs for a specific vendor"""
        database = self.load_database()
        return set(database["vendors"].get(vendor, [])) 