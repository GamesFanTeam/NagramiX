#!/usr/bin/env python3
"""Apply the smallest possible NagramiX branding layer to Telegram-iOS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
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
    icon_sources = Path(__file__).with_name("branding") / "icons"
    icon_source = icon_sources / "1.png"
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

    alternate_icons = [
        ("NagramiXMain", "1.png"),
        ("NagramiXNeon", "2.png"),
        ("NagramiXAmethyst", "3.png"),
        ("NagramiXSilver", "4.png"),
        ("NagramiXLime", "5.png"),
        ("NagramiXFlame", "6.png"),
        ("NagramiXSunset", "7.png"),
        ("NagramiXRuby", "8.png"),
    ]
    alternate_sizes = [
        ("@2x", 120),
        ("@3x", 180),
        ("-76", 76),
        ("-76@2x", 152),
        ("-83.5@2x", 167),
        ("_29x29", 29),
        ("_58x58", 58),
        ("_80x80", 80),
        ("_87x87", 87),
        ("_notification", 20),
        ("_notification@2x", 40),
        ("_notification@3x", 60),
    ]
    for icon_name, source_name in alternate_icons:
        source_path = icon_sources / source_name
        target_dir = source / "Telegram" / "Telegram-iOS" / f"{icon_name}.alticon"
        target_dir.mkdir(parents=True, exist_ok=True)
        for suffix, size in alternate_sizes:
            target_path = target_dir / f"{icon_name}{suffix}.png"
            try:
                from PIL import Image

                with Image.open(source_path) as image:
                    image.resize((size, size), Image.Resampling.LANCZOS).save(target_path, format="PNG")
            except ImportError:
                subprocess.run(
                    ["/usr/bin/sips", "-z", str(size), str(size), str(source_path), "--out", str(target_path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )

    build_file = source / "Telegram" / "BUILD"
    old_icon_folders = """alternate_icon_folders = [
    "BlackIcon",
    "BlackClassicIcon",
    "BlackFilledIcon",
    "BlueIcon",
    "BlueClassicIcon",
    "BlueFilledIcon",
    "WhiteFilledIcon",
    "New1",
    "New2",
    "Premium",
    "PremiumBlack",
    "PremiumTurbo",
]
"""
    new_icon_folders = """alternate_icon_folders = [
    "NagramiXMain",
    "NagramiXNeon",
    "NagramiXAmethyst",
    "NagramiXSilver",
    "NagramiXLime",
    "NagramiXFlame",
    "NagramiXSunset",
    "NagramiXRuby",
]
"""
    if not replace_text(build_file, old_icon_folders, new_icon_folders):
        raise SystemExit("Pinned alternate-icon BUILD anchor was not found")

    app_delegate = source / "submodules" / "TelegramUI" / "Sources" / "AppDelegate.swift"
    old_available_icons = """                var icons = [
                    PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: buildConfig.isAppStoreBuild),
                    PresentationAppIcon(name: "New2", imageName: "New2"),
                    PresentationAppIcon(name: "New1", imageName: "New1"),
                    PresentationAppIcon(name: "BlackIcon", imageName: "BlackIcon"),
                    PresentationAppIcon(name: "BlueClassicIcon", imageName: "BlueClassicIcon"),
                    PresentationAppIcon(name: "BlackClassicIcon", imageName: "BlackClassicIcon"),
                    PresentationAppIcon(name: "BlueFilledIcon", imageName: "BlueFilledIcon"),
                    PresentationAppIcon(name: "BlackFilledIcon", imageName: "BlackFilledIcon")
                ]
                if buildConfig.isInternalBuild {
                    icons.append(PresentationAppIcon(name: "WhiteFilledIcon", imageName: "WhiteFilledIcon"))
                }
""" + "                \n" + """                icons.append(PresentationAppIcon(name: "Premium", imageName: "Premium", isPremium: true))
                icons.append(PresentationAppIcon(name: "PremiumTurbo", imageName: "PremiumTurbo", isPremium: true))
                icons.append(PresentationAppIcon(name: "PremiumBlack", imageName: "PremiumBlack", isPremium: true))
""" + "                \n" + """                return icons
"""
    new_available_icons = """                return [
                    PresentationAppIcon(name: "NagramiXMain", imageName: "NagramiXMain", isDefault: true),
                    PresentationAppIcon(name: "NagramiXNeon", imageName: "NagramiXNeon"),
                    PresentationAppIcon(name: "NagramiXAmethyst", imageName: "NagramiXAmethyst"),
                    PresentationAppIcon(name: "NagramiXSilver", imageName: "NagramiXSilver"),
                    PresentationAppIcon(name: "NagramiXLime", imageName: "NagramiXLime"),
                    PresentationAppIcon(name: "NagramiXFlame", imageName: "NagramiXFlame"),
                    PresentationAppIcon(name: "NagramiXSunset", imageName: "NagramiXSunset"),
                    PresentationAppIcon(name: "NagramiXRuby", imageName: "NagramiXRuby")
                ]
"""
    if not replace_text(app_delegate, old_available_icons, new_available_icons):
        raise SystemExit("Pinned available alternate-icon anchor was not found")

    icon_ui = source / "submodules" / "SettingsUI" / "Sources" / "Themes" / "ThemeSettingsAppIconItem.swift"
    icon_name_anchor = """                            var name = "Icon"
                            var bordered = true
                            switch icon.name {
"""
    icon_name_replacement = """                            var name = "Icon"
                            var bordered = true
                            let isRussian = item.strings.baseLanguageCode == "ru"
                            switch icon.name {
                                case "NagramiXMain":
                                    name = isRussian ? "Основная" : "Main"
                                case "NagramiXNeon":
                                    name = isRussian ? "Неон" : "Neon"
                                case "NagramiXAmethyst":
                                    name = isRussian ? "Аметист" : "Amethyst"
                                case "NagramiXSilver":
                                    name = isRussian ? "Серебро" : "Silver"
                                case "NagramiXLime":
                                    name = isRussian ? "Лайм" : "Lime"
                                case "NagramiXFlame":
                                    name = isRussian ? "Пламя" : "Flame"
                                case "NagramiXSunset":
                                    name = isRussian ? "Закат" : "Sunset"
                                case "NagramiXRuby":
                                    name = isRussian ? "Рубин" : "Ruby"
"""
    if not replace_text(icon_ui, icon_name_anchor, icon_name_replacement):
        raise SystemExit("Pinned app-icon title anchor was not found")

    apply_features(source)

    print(f"Generated configuration: {args.configuration}")
    print(f"Applied NagramiX app icon: {icon_source}")
    print("Applied 8 NagramiX app icon choices")


if __name__ == "__main__":
    main()
