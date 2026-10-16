"""Command-line interface for kv-to-sx converter."""

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from .engine import MappingEngine
from .exceptions import KvToSxError

__version__ = "0.1.0"


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="kv-to-sx",
        description="Convert BISON KV messages (KV15, KV7/8, KV17) into SIRI-SX messages using a TOML mapping file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a KV17 XML file using mapping.toml and write to stdout:
  kv-to-sx message.xml

  # Convert from stdin in a pipeline:
  cat message.xml | kv-to-sx

  # Specify a custom mapping configuration file:
  kv-to-sx -m custom_mapping.toml message.xml

  # Write output directly to a file:
  kv-to-sx message.xml -o output_siri.xml
""",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="-",
        metavar="INPUT_FILE",
        help="Path to input KV XML file (reads from stdin if omitted or '-')",
    )
    parser.add_argument(
        "-m",
        "--mapping",
        default="mapping.toml",
        metavar="FILE",
        help="Path to TOML mapping configuration file (default: mapping.toml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="Path to output file (default: stdout)",
    )
    parser.add_argument(
        "--source-message",
        default=None,
        metavar="TYPE",
        help="Override auto-detected source message type (e.g. KV17cvlinfo, KV8generalmessages, KV15)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entrypoint for the kv-to-sx CLI."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Load mapping configuration
    mapping_path = Path(parsed_args.mapping)
    if not mapping_path.exists():
        # Fall back to looking next to the package or current working directory
        print(
            f"Error: Mapping configuration file '{mapping_path}' not found.",
            file=sys.stderr,
        )
        return 1

    try:
        engine = MappingEngine.from_toml_file(mapping_path)
    except Exception as e:
        print(f"Error loading mapping configuration: {e}", file=sys.stderr)
        return 1

    # Read input XML
    try:
        if parsed_args.input_file == "-":
            input_content = sys.stdin.read()
            if not input_content.strip():
                print("Error: Standard input is empty.", file=sys.stderr)
                return 1
        else:
            input_path = Path(parsed_args.input_file)
            if not input_path.exists():
                print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
                return 1
            input_content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1

    # Perform conversion
    try:
        siri_xml = engine.convert(
            input_content,
            source_message=parsed_args.source_message,
        )
    except KvToSxError as e:
        print(f"Conversion error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    # Write output
    try:
        if parsed_args.output:
            out_path = Path(parsed_args.output)
            out_path.write_text(siri_xml, encoding="utf-8")
        else:
            sys.stdout.write(siri_xml)
            if not siri_xml.endswith("\n"):
                sys.stdout.write("\n")
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
