#!/bin/bash
set -euo pipefail

APP_PATH="${1:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa bundle.id}"
OUTPUT_PATH="${2:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa bundle.id}"
TARGET_BUNDLE_ID="${3:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa bundle.id}"
UPSTREAM_BUNDLE_ID="ph.telegra.Telegraph"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Application bundle not found: $APP_PATH" >&2
  exit 1
fi

rm -rf .nagramix-package
rm -f "$OUTPUT_PATH"
mkdir -p .nagramix-package/Payload
cp -R "$APP_PATH" .nagramix-package/Payload/NagramiX.app
find .nagramix-package/Payload/NagramiX.app -name '_CodeSignature' -type d -prune -exec rm -rf {} +
find .nagramix-package/Payload/NagramiX.app -name 'embedded.mobileprovision' -type f -delete

python3 "$SCRIPT_DIR/../nagramix/rewrite_bundle_ids.py" \
  .nagramix-package/Payload/NagramiX.app \
  --upstream "$UPSTREAM_BUNDLE_ID" \
  --target "$TARGET_BUNDLE_ID"

final_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' .nagramix-package/Payload/NagramiX.app/Info.plist)"
test "$final_id" = "$TARGET_BUNDLE_ID" || { echo "Unexpected final bundle id: $final_id" >&2; exit 1; }
(
  cd .nagramix-package
  /usr/bin/zip -qry "../$OUTPUT_PATH" Payload
)
echo "Created unsigned IPA: $OUTPUT_PATH ($final_id)"
