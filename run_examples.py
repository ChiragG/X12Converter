#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ANSI color codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'reset': '\033[0m',
    'bold': '\033[1m'
}

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"{COLORS['bold']} {text} {COLORS['reset']}".center(80, "="))
    print("=" * 80)

def print_success(text):
    """Print a success message."""
    print(f"\n{COLORS['green']}✓ {text}{COLORS['reset']}")

def print_error(text):
    """Print an error message."""
    print(f"\n{COLORS['red']}✗ {text}{COLORS['reset']}")

def print_warning(text):
    """Print a warning message."""
    print(f"\n{COLORS['yellow']}⚠ {text}{COLORS['reset']}")

def ensure_diff_dir():
    """Ensure the diff directory exists."""
    diff_dir = Path("diffs")
    diff_dir.mkdir(exist_ok=True)
    return diff_dir

def get_diff_command():
    """Get the appropriate diff command with color support."""
    # Try colordiff first
    if subprocess.run(['which', 'colordiff'], capture_output=True).returncode == 0:
        return ['colordiff']
    # Fall back to diff with color
    return ['diff', '--color=auto']

def run_conversion_and_compare(json_file, edi_file):
    """Run the JSON to EDI conversion and compare with example file."""
    json_name = os.path.basename(json_file)
    print_header(f"Processing {json_name}")
    
    # Create a unique output filename based on the input file
    output_file = f"output_{os.path.splitext(json_name)[0]}.837"
    
    # Run the conversion
    try:
        subprocess.run([sys.executable, "json_to_edi.py", json_file, output_file], check=True)
        print_success("Conversion completed successfully")
    except subprocess.CalledProcessError as e:
        print_error(f"Conversion failed: {e}")
        return

    # Compare with example file
    try:
        diff_cmd = get_diff_command()
        result = subprocess.run(diff_cmd + [output_file, edi_file], capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Generated file matches example file exactly")
        else:
            print_warning("Generated file differs from example file:")
            print("\nDifferences found:")
            print("-" * 80)
            # Use subprocess.Popen to preserve color output
            diff_process = subprocess.Popen(
                diff_cmd + [output_file, edi_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            diff_output, _ = diff_process.communicate()
            print(diff_output)
            print("-" * 80)
            
            # Save the differences to a file in the diffs directory
            diff_dir = ensure_diff_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_file = diff_dir / f"diff_{os.path.splitext(json_name)[0]}_{timestamp}.txt"
            with open(diff_file, "w") as f:
                f.write(result.stdout)
            print(f"\nDifferences saved to: {COLORS['blue']}{diff_file}{COLORS['reset']}")
    except subprocess.CalledProcessError as e:
        print_error(f"Comparison failed: {e}")

def main():
    examples_dir = Path("examples")
    examples = [
        ("mojo_dojo_casa_house.json", "mojo_dojo_casa_house.837"),
        ("multi_procedure_barbie.json", "multi_procedure_barbie.837"),
        ("subscriber_with_a_dekendent.json", "subscriber_with_a_dekendent.837")
    ]

    print_header("JSON to EDI 837P Conversion Test Suite")
    print("\nThis script will:")
    print("1. Convert each example JSON file to EDI format")
    print("2. Compare the generated output with the corresponding example EDI file")
    print("3. Display any differences found with color highlighting")
    print("4. Save differences to separate files in the 'diffs' directory")

    for json_file, edi_file in examples:
        json_path = examples_dir / json_file
        edi_path = examples_dir / edi_file
        
        if not json_path.exists() or not edi_path.exists():
            print_error(f"Missing files for {json_file}")
            continue

        run_conversion_and_compare(str(json_path), str(edi_path))

if __name__ == "__main__":
    main() 