#!/usr/bin/env python3
"""Apply the smallest possible NagramiX branding layer to Telegram-iOS."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def replace_text(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    if old not in content:
        return False
    path.write_text(content.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--configuration", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    if not (source / "Telegram" / "BUILD").exists() and not (source / "Telegram" / "BUILD.bazel").exists():
        raise SystemExit(f"Not a Telegram-iOS source tree: {source}")

    api_id = os.environ.get("TELEGRAM_API_ID", "")
    api_hash = os.environ.get("TELEGRAM_API_HASH", "")
    if not api_id.isdigit() or not api_hash:
        raise SystemExit("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured")

    template = Path(__file__).with_name("configuration.template.json")
    configuration = json.loads(template.read_text(encoding="utf-8"))
    configuration["api_id"] = api_id
    configuration["api_hash"] = api_hash
    args.configuration.parent.mkdir(parents=True, exist_ok=True)
    args.configuration.write_text(json.dumps(configuration, indent=2) + "\n", encoding="utf-8")

    # This exact fragment is pinned to the audited Telegram-iOS commit. Failing
    # instead of guessing prevents a silent loss of branding after an update.
    build_file = source / "Telegram" / "BUILD"
    old_fragment = "<key>CFBundleDisplayName</key>\n    <string>Telegram</string>"
    new_fragment = "<key>CFBundleDisplayName</key>\n    <string>NagramiX</string>"
    if not replace_text(build_file, old_fragment, new_fragment):
        raise SystemExit("Pinned CFBundleDisplayName fragment was not found")

    # Build the device app with its real identifier and generated build-only
    # profiles. Extensions stay out of the first login checkpoint.
    make_file = source / "build-system" / "Make" / "Make.py"
    anchor = "    bazel_command_line.set_configuration(arguments.configuration)"
    replacement = """    bazel_command_line.common_build_args += ['--//Telegram:disableExtensions']
    bazel_command_line.set_configuration(arguments.configuration)"""
    if not replace_text(make_file, anchor, replacement):
        raise SystemExit("Pinned unsigned-build anchor was not found in Make.py")

    print(f"Generated configuration: {args.configuration}")


if __name__ == "__main__":
    main()
