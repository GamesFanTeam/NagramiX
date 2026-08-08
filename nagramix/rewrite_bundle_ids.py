#!/usr/bin/env python3
"""Rewrite upstream identifiers in every plist inside an unsigned app bundle."""

from __future__ import annotations

import argparse
import plistlib
from pathlib import Path
from typing import Any


def rewrite(value: Any, upstream: str, target: str) -> Any:
    if isinstance(value, str):
        return value.replace(upstream, target)
    if isinstance(value, list):
        return [rewrite(item, upstream, target) for item in value]
    if isinstance(value, dict):
        return {key: rewrite(item, upstream, target) for key, item in value.items()}
    return value


def contains(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, list):
        return any(contains(item, needle) for item in value)
    if isinstance(value, dict):
        return any(contains(item, needle) for item in value.values())
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    app = args.app.resolve()
    plists = sorted(app.rglob("Info.plist"))
    if not plists:
        raise SystemExit(f"No Info.plist files found under {app}")

    for path in plists:
        with path.open("rb") as stream:
            data = plistlib.load(stream)
        updated = rewrite(data, args.upstream, args.target)
        if path == app / "Info.plist":
            updated["CFBundleDisplayName"] = "NagramiX"
        with path.open("wb") as stream:
            plistlib.dump(updated, stream, fmt=plistlib.FMT_BINARY, sort_keys=False)

    remaining = []
    for path in plists:
        with path.open("rb") as stream:
            data = plistlib.load(stream)
        if contains(data, args.upstream):
            remaining.append(str(path.relative_to(app)))
    if remaining:
        raise SystemExit("Upstream identifier remains in: " + ", ".join(remaining))

    with (app / "Info.plist").open("rb") as stream:
        main_plist = plistlib.load(stream)
    final_id = main_plist.get("CFBundleIdentifier")
    if final_id != args.target:
        raise SystemExit(f"Unexpected final bundle id: {final_id}")
    print(f"Rewrote {len(plists)} plist files; final bundle id: {final_id}")


if __name__ == "__main__":
    main()
