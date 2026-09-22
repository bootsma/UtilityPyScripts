#!/usr/bin/env python3

import argparse
import json
import platform
import shutil
import subprocess
import sys
from argparse import RawTextHelpFormatter
from datetime import datetime
from pathlib import Path


def check_conda_pack():
    """Return True if conda-pack is available."""
    return shutil.which("conda-pack") is not None


def main():

    parser = argparse.ArgumentParser(
        description="Backup Conda environments to YAML and optional conda-pack archives.",
        formatter_class=RawTextHelpFormatter,
    )

    parser.add_argument(
        "-o", "--output", required=True, type=Path, help="Output directory."
    )

    parser.add_argument(
        "-c",
        "--conda",
        default="conda",
        help="Path to conda executable. Defaults to 'conda' in PATH.",
    )

    type_help = (
        "Export type:\n"
        "  default      : Exact environment including build strings.\n"
        "  no-builds    : Removes build strings but preserves versions.\n"
        "  from-history : User-installed Conda packages only.\n"
        "  all-types    : Export all three formats."
    )

    parser.add_argument(
        "-t",
        "--type",
        choices=["default", "no-builds", "from-history", "all-types"],
        default="default",
        help=type_help,
    )

    parser.add_argument(
        "--timestamp", action="store_true", help="Append timestamp to backup filenames."
    )

    parser.add_argument(
        "--skip-base", action="store_true", help="Skip backing up the base environment."
    )

    parser.add_argument(
        "--pack", action="store_true", help="Create conda-pack archive backups."
    )

    parser.add_argument(
        "--pack-format",
        choices=["tar.gz", "zip"],
        default=None,
        help="Archive format. Default: zip on Windows, tar.gz elsewhere.",
    )

    args = parser.parse_args()

    yaml_dir = args.output / "yaml"
    pack_dir = args.output / "packed"

    yaml_dir.mkdir(parents=True, exist_ok=True)

    if args.pack:
        pack_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.conda == "conda":
            import shutil

            conda_cmd = shutil.which(args.conda)
            if conda_cmd is None:
                print(f"ERROR: Conda executable '{args.conda}' was not found in PATH.")
                sys.exit(1)
            args.conda = conda_cmd

        result = subprocess.run(
            [args.conda, "info", "--json"], capture_output=True, text=True, check=True
        )

        info = json.loads(result.stdout)

    except FileNotFoundError:
        print(f"ERROR: Conda executable '{args.conda}' was not found.")
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"ERROR running conda:\n{e.stderr}")
        sys.exit(1)

    root_prefix = info.get("root_prefix", "")
    envs = info.get("envs", [])

    if not envs:
        print("No Conda environments found.")
        sys.exit(0)

    timestamp_str = (
        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if args.timestamp else ""
    )

    #
    # FIXED LOGIC
    #
    if args.type == "all-types":
        type_list = ["default", "no-builds", "from-history"]
    else:
        type_list = [args.type]

    conda_pack_available = False

    if args.pack:
        conda_pack_available = check_conda_pack()

        if not conda_pack_available:
            print(
                "\nWARNING: conda-pack was requested but "
                "is not installed.\n"
                "Only YAML backups will be generated.\n"
            )

    #
    # Process each environment
    #
    for env_path in envs:
        if env_path == root_prefix:
            if args.skip_base:
                print("Skipping base environment...")
                continue

            env_name = "base"

        else:
            env_name = Path(env_path).name

        print(f"\nProcessing environment: {env_name}")

        #
        # YAML exports
        #
        for export_type in type_list:
            if export_type == "default":
                type_suffix = f"_{platform.system().lower()}"
            else:
                type_suffix = f"_{export_type}"

            output_file = yaml_dir / f"{env_name}{type_suffix}{timestamp_str}.yml"

            export_cmd = [
                args.conda,
                "env",
                "export",
                "-p",
                env_path,
                "--format",
                "yaml",
            ]

            if export_type == "no-builds":
                export_cmd.append("--no-builds")

            elif export_type == "from-history":
                export_cmd.append("--from-history")

            export_cmd.extend(["-f", str(output_file)])

            print(f"  Exporting {output_file.name}")

            try:
                subprocess.run(export_cmd, capture_output=True, text=True, check=True)

            except subprocess.CalledProcessError as e:
                print(f"  FAILED YAML export for {env_name}\n  {e.stderr.strip()}")
                raise

        #
        # Conda-pack export
        #
        if args.pack and conda_pack_available:
            archive_ext = args.pack_format

            if archive_ext is None:
                archive_ext = "zip" if platform.system() == "Windows" else "tar.gz"

            archive_file = pack_dir / f"{env_name}{timestamp_str}.{archive_ext}"

            pack_cmd = ["conda-pack", "-p", env_path, "-o", str(archive_file)]

            print(f"  Packing {archive_file.name}")

            try:
                subprocess.run(pack_cmd, capture_output=True, text=True, check=True)

            except subprocess.CalledProcessError as e:
                print(
                    f"  FAILED conda-pack export for {env_name}\n  {e.stderr.strip()}"
                )

    print("\nBackup complete.")


if __name__ == "__main__":
    main()
