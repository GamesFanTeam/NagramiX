#!/usr/bin/env python3
"""Apply the smallest possible NagramiX branding layer to Telegram-iOS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from apply_features import apply_features


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

    # Replace the primary Icon Composer layer with the official NagramiX asset.
    # Icon Composer generates every required iPhone/iPad size during the build.
    icon_source = Path(__file__).with_name("branding") / "NagramiX-AppIcon.png"
    icon_bundle = source / "Telegram" / "Telegram-iOS" / "Telegram.icon"
    icon_assets = icon_bundle / "Assets"
    icon_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(icon_source, icon_assets / "NagramiX-AppIcon.png")
    icon_manifest_path = icon_bundle / "icon.json"
    icon_manifest = json.loads(icon_manifest_path.read_text(encoding="utf-8"))
    icon_manifest["groups"][0]["layers"] = [
        {
            "blend-mode-specializations": [{"value": "normal"}],
            "glass": False,
            "image-name": "NagramiX-AppIcon.png",
            "name": "NagramiX",
        }
    ]
    icon_manifest["groups"][0]["blur-material"] = 0
    icon_manifest["groups"][0]["specular"] = False
    icon_manifest_path.write_text(json.dumps(icon_manifest, indent=2) + "\n", encoding="utf-8")

    apply_features(source)

    print(f"Generated configuration: {args.configuration}")
    print(f"Applied NagramiX app icon: {icon_source}")


if __name__ == "__main__":
    main()
