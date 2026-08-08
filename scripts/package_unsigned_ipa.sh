#!/bin/bash
set -euo pipefail

APP_PATH="${1:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa}"
OUTPUT_PATH="${2:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa}"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Application bundle not found: $APP_PATH" >&2
  exit 1
fi

rm -rf .nagramix-package
rm -f "$OUTPUT_PATH"
mkdir -p .nagramix-package/Payload
cp -R "$APP_PATH" .nagramix-package/Payload/NagramiX.app
find .nagramix-package/Payload/NagramiX.app -name '_CodeSignature' -type d -prune -exec rm -rf {} +
rm -f .nagramix-package/Payload/NagramiX.app/embedded.mobileprovision
(
  cd .nagramix-package
  /usr/bin/zip -qry "../$OUTPUT_PATH" Payload
)
echo "Created unsigned IPA: $OUTPUT_PATH"
