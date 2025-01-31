import json
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

# Configure your paths here
MASTER_JSONL = "/path/to/master/list"
IMAGE_SOURCE = "/path/to/image/folder"
PUBLISHED_JSONL = "/path/to/jsonl/site/inventory"
ASSETS_FOLDER = "/path/to/site/asset/folder"


class DaylilyProcessor:
    def __init__(self):
        self.master_jsonl = Path(MASTER_JSONL)
        self.image_source = Path(IMAGE_SOURCE)
        self.published_jsonl = Path(PUBLISHED_JSONL)
        self.assets_folder = Path(ASSETS_FOLDER)
        self.pending_additions = []
        self.pending_removals = []
        self._validate_setup()

    def _validate_setup(self):
        if not self.master_jsonl.exists():
            raise FileNotFoundError(f"Master JSONL file not found: {self.master_jsonl}")
        self.assets_folder.mkdir(parents=True, exist_ok=True)
        self.published_jsonl.parent.mkdir(parents=True, exist_ok=True)
        if not self.published_jsonl.exists():
            with open(self.published_jsonl, 'w', encoding='utf-8') as f:
                pass

    def read_master_data(self) -> List[Dict]:
        entries = []
        try:
            if not self.master_jsonl.exists():
                print(f"Master file not found: {self.master_jsonl}")
                return entries

            with open(self.master_jsonl, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if isinstance(entry, dict) and 'name' in entry:
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading master file: {e}")
        return entries

    def read_published_data(self) -> List[Dict]:
        """Read published data with Unicode support"""
        entries = []
        try:
            with open(self.published_jsonl, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"Warning: Invalid JSON at line {line_num}: {e}")
                            continue
        except Exception as e:
            print(f"Error reading published file: {e}")
        return entries

    def get_image_name(self, url: str) -> Optional[str]:
        """Extract image name from URL, handling Unicode and special characters"""
        if not url or url.lower() == 'none' or 'no image available' in url.lower():
            return None
        try:
            name = unquote(url.split('/')[-1])  # Add URL decoding
            return name if name and name.lower() != 'none' else None
        except:
            return None

    def get_image_variations(self, variety_name: str, url_image_name: str) -> List[str]:
        """Generate possible image filenames from variety name and URL"""
        variations = []

        # Original URL image name
        if url_image_name:
            variations.append(url_image_name)

        # Simple variety_name.jpg
        if variety_name:
            simple_name = f"{variety_name}.jpg"
            if simple_name not in variations:
                variations.append(simple_name)

        return variations

    def copy_image(self, variety_name: str, url_image_name: str) -> Tuple[bool, str]:
        """Try to copy image using both names, returns success flag and used filename"""
        # Try URL image name first
        if url_image_name:
            source = self.image_source / url_image_name
            if source.exists():
                destination = self.assets_folder / url_image_name
                try:
                    shutil.copy2(source, destination)
                    return True, url_image_name
                except Exception as e:
                    print(f"Error copying URL image: {e}")

        # Try variety name.jpg
        if variety_name:
            simple_name = f"{variety_name}.jpg"
            source = self.image_source / simple_name
            if source.exists():
                destination = self.assets_folder / simple_name
                try:
                    shutil.copy2(source, destination)
                    return True, simple_name
                except Exception as e:
                    print(f"Error copying variety name image: {e}")

        return False, "placeholder.jpg"  # Return a default filename instead of None

    def clean_entry(self, entry: Dict) -> Dict:
        """Clean entry and handle image URL"""
        if not entry:
            return {}

        cleaned = entry.copy()
        cleaned.pop('scraped_at', None)

        # Get original image name from URL
        url_image_name = self.get_image_name(entry.get('image_url', ''))

        # Try to copy the image using both names
        success, used_name = self.copy_image(
            variety_name=entry.get('name', ''),
            url_image_name=url_image_name or ''  # Handle None case
        )

        cleaned['image_url'] = used_name  # Will always have a value now
        return cleaned

    def validate_variety(self, variety: Dict) -> bool:
        """Validate required fields exist"""
        required_fields = ['name', 'hybridizer', 'year']
        missing_fields = [field for field in required_fields if not variety.get(field)]

        if missing_fields:
            print(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        return True

    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        return ' '.join(name.lower().split())

    def find_variety(self, variety_name: str) -> Tuple[Optional[Dict], bool]:
        if not variety_name:
            return None, False

        normalized_name = self.normalize_name(variety_name)

        # Check published list
        published_data = self.read_published_data()
        for item in published_data:
            if isinstance(item, dict) and item.get('name') and self.normalize_name(item['name']) == normalized_name:
                return item, True

        # Check master list
        master_data = self.read_master_data()
        master_variety = None
        for item in master_data:
            if isinstance(item, dict) and item.get('name') and self.normalize_name(item['name']) == normalized_name:
                master_variety = item
                break

        if not master_variety:
            similar_names = self.find_similar_names(variety_name)
            if similar_names:
                print("\nDid you mean one of these?")
                for name in similar_names:
                    print(f"- {name}")

        return master_variety, False

    def find_similar_names(self, variety_name: str) -> List[str]:
        """Find similar names using substring matching"""
        all_varieties = self.read_master_data()
        similar_names = []

        normalized_search = self.normalize_name(variety_name)
        words = normalized_search.split()

        for variety in all_varieties:
            current_name = self.normalize_name(variety['name'])
            if any(word in current_name for word in words):
                similar_names.append(variety['name'])

        return similar_names[:5]

    def process_variety(self, variety_name: str) -> bool:
        """Process a variety entry"""
        if not variety_name:
            print("\nProcessing pending changes...")
            self.commit_changes()
            return False

        variety, is_published = self.find_variety(variety_name)

        if not variety:
            print(f"\nVariety '{variety_name}' not found.")
            return True

        if is_published:
            print("\nThis variety is currently in the published list:")
            self.print_variety(variety)
            if input("\nWould you like to remove this variety? (y/n): ").lower() == 'y':
                self.pending_removals.append(variety['name'])
                print(f"Marked '{variety['name']}' for removal")
        else:
            if not self.validate_variety(variety):
                print("Cannot add variety due to missing required fields")
                return True

            print("\nVariety found in master list:")
            self.print_variety(variety)
            if input("\nWould you like to add this variety? (y/n): ").lower() == 'y':
                self.pending_additions.append(variety['name'])
                print(f"Marked '{variety['name']}' for addition")

        return True

    def print_variety(self, variety: Dict) -> None:
        print("\n=== Variety Details ===")
        for key, value in variety.items():
            if key != 'scraped_at':
                print(f"{key}: {value}")
        print("=====================")

    def commit_changes(self) -> None:
        if not self.pending_additions and not self.pending_removals:
            print("\nNo changes to commit")
            return

        print("\nCommitting changes...")
        published_data = self.read_published_data()

        # Process removals
        for variety_name in self.pending_removals:
            try:
                variety = next((item for item in published_data
                                if isinstance(item, dict) and item.get('name') == variety_name), None)
                if variety and variety.get('image_url'):
                    image_path = self.assets_folder / variety['image_url']
                    if image_path.exists() and variety['image_url'] != 'no-image.jpg':
                        try:
                            image_path.unlink()
                        except Exception as e:
                            print(f"Warning: Could not remove image {variety['image_url']}: {e}")

                published_data = [item for item in published_data
                                  if isinstance(item, dict) and item.get('name') != variety_name]
                print(f"Removed: {variety_name}")
            except Exception as e:
                print(f"Error removing {variety_name}: {e}")

        # Process additions (existing code remains the same)
        master_data = self.read_master_data()
        for variety_name in self.pending_additions:
            try:
                variety = next((item for item in master_data if item.get('name') == variety_name), None)
                if variety and self.validate_variety(variety):
                    cleaned_entry = self.clean_entry(variety)
                    published_data.append(cleaned_entry)
                    print(f"Added: {variety_name}")
            except Exception as e:
                print(f"Error adding {variety_name}: {e}")

        try:
            with open(self.published_jsonl, 'w', encoding='utf-8') as f:
                for entry in published_data:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            print("\nAll changes committed successfully")
        except Exception as e:
            print(f"Error writing to published file: {e}")
            return

        self.pending_additions = []
        self.pending_removals = []


def main():
    try:
        processor = DaylilyProcessor()

        print("\nDaylily Gallery Manager")
        print("Enter variety names to process them")
        print("Press Enter with no input to commit changes and exit")
        print("\nCurrent paths:")
        print(f"Master JSONL: {MASTER_JSONL}")
        print(f"Image Source: {IMAGE_SOURCE}")
        print(f"Published JSONL: {PUBLISHED_JSONL}")
        print(f"Assets Folder: {ASSETS_FOLDER}")

        while True:
            try:
                variety_name = input("\nEnter variety name: ").strip()
                if not processor.process_variety(variety_name):
                    break
            except KeyboardInterrupt:
                print("\nOperation cancelled by user")
                break
            except Exception as e:
                print(f"Error processing variety: {e}")
                if input("Continue? (y/n): ").lower() != 'y':
                    break
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == '__main__':
    main()