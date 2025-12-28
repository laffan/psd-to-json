import json
import os
import sys
import time
import argparse
from .src.core.psd_processor import PSDProcessor
from .src.core.json_generator import JSONGenerator
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG to capture all levels of log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the log message format
    handlers=[
        logging.StreamHandler()  # Add a StreamHandler to output log messages to the console
    ]
)

def get_file_mtime(filepath):
    try:
        return os.stat(filepath).st_mtime
    except FileNotFoundError:
        return 0

def load_config():
    config_path = os.path.join(os.getcwd(), 'psd-to-json.config')
    
    if not os.path.exists(config_path):
        error_message = f"""
Error: No psd-to-json.config file found in the current directory.

Please create a psd-to-json.config file with the following structure:
{{
  "output_dir": "path/to/assets/folder",
  "psd_files": [
    "path/to/demo.psd"
  ],
  "tile_slice_size": 500,
  "tile_scaled_versions": [100],
  "generateOnSave": false,
  "pngQualityRange": {{
    "low": 85,
    "high": 90
  }},
  "jpgQuality": 80,
  "ignoreLayers": []
}}

All paths should be relative to the current directory.
        """
        print(error_message.strip())
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in psd-to-json.config: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

def process_psds(config):
    # Ensure output directory exists
    os.makedirs(config['output_dir'], exist_ok=True)
    print(f"Configuration in main.py/process_psds: {config}")

    # Process PSD files
    processor = PSDProcessor(config)
    processed_data = processor.process_all_psds()
    
    # Generate JSON output
    generator = JSONGenerator(config, processed_data)
    generator.generate_json()

def main():
    parser = argparse.ArgumentParser(description='Convert PSD files to JSON with optimized assets')
    parser.add_argument('--watch', action='store_true',
                       help='Enable watching for file changes (overrides generateOnSave setting)')
    parser.add_argument('--metadata-only', action='store_true',
                       help='Only generate JSON metadata without processing images')

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Override generateOnSave if --watch flag is provided
    if args.watch:
        config['generateOnSave'] = True
        print("Watch mode enabled via command line argument")

    # Set metadata-only mode
    if args.metadata_only:
        config['metadataOnly'] = True
        print("Metadata-only mode enabled - skipping image processing")

    # Initial processing
    process_psds(config)

    if config.get('generateOnSave', False):
        print("Watching for PSD file changes...")
        last_modified_times = {psd: get_file_mtime(psd) for psd in config['psd_files']}

        try:
            while True:
                changes_detected = False
                for psd in config['psd_files']:
                    current_mtime = get_file_mtime(psd)
                    if current_mtime > last_modified_times[psd]:
                        print(f"Change detected in {psd}")
                        changes_detected = True
                        last_modified_times[psd] = current_mtime

                if changes_detected:
                    process_psds(config)
                    print("Processing complete. Watching for more changes...")

                time.sleep(2)  # Wait for 2 seconds before checking again
        except KeyboardInterrupt:
            print("Stopping file watcher...")

if __name__ == "__main__":
    main()