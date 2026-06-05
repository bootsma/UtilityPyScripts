#!/usr/bin/env python3
import argparse
import subprocess
import json
import sys
import platform
from pathlib import Path
from datetime import datetime
from argparse import RawTextHelpFormatter


def main():
    parser = argparse.ArgumentParser(
        description="Backup all Conda environments to YAML files.",
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-o', '--output', required=True, type=Path,
                        help="Required: Output folder location for the YAML files.")
    parser.add_argument('-c', '--conda', default='conda',
                        help="Optional: Path to the conda executable. Defaults to 'conda' in PATH.")

    type_help = (
        "Optional: Export type.\n"
        "  'default'      : Exact match including OS-specific build strings. Fails on different OS. Includes pip packages.\n"
        "  'no-builds'    : Strips OS-specific build strings but keeps exact versions. Best for cross-platform matching. Includes pip packages.\n"
        "  'from-history' : Only explicitly installed Conda packages. Best cross-platform resolve, but completely IGNORES pip packages."
    )
    parser.add_argument('-t', '--type', choices=['default', 'no-builds', 'from-history'], default='default',
                        help=type_help)

    parser.add_argument('--timestamp', action='store_true',
                        help="Optional: Append the current timestamp to the output filenames.")
    parser.add_argument('--skip-base', action='store_true',
                        help="Optional: Skip exporting the base environment.")

    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run([args.conda, 'info', '--json'], capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
    except FileNotFoundError:
        print(f"Error: Conda executable '{args.conda}' not found. Use -c to specify the full path.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to run Conda.\n{e.stderr}")
        sys.exit(1)

    root_prefix = info.get('root_prefix', '')
    envs = info.get('envs', [])

    if not envs:
        print("No Conda environments found.")
        sys.exit(0)

    timestamp_str = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if args.timestamp else ""

    # Determine the type string for the filename
    if args.type == 'default':
        # platform.system() returns 'Windows', 'Linux', or 'Darwin' (macOS)
        type_str = f"_{platform.system().lower()}"
    else:
        type_str = f"_{args.type}"

    for env_path in envs:
        if env_path == root_prefix:
            if args.skip_base:
                print("Skipping 'base' environment...")
                continue
            env_name = "base"
        else:
            env_name = Path(env_path).name

        output_file = args.output / f"{env_name}{type_str}{timestamp_str}.yml"
        print(f"Exporting '{env_name}' to {output_file}...")

        export_cmd = [args.conda, 'env', 'export', '-p', env_path]

        if args.type == 'no-builds':
            export_cmd.append('--no-builds')
        elif args.type == 'from-history':
            export_cmd.append('--from-history')

        export_cmd.extend(['-f', str(output_file)])

        try:
            subprocess.run(export_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"  Failed to export '{env_name}'. Error:\n  {e.stderr.strip()}")

    print("\nAll environments backed up successfully.")


if __name__ == "__main__":
    main()