#!/bin/bash
set -euo pipefail

APP_PATH="${1:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa bundle.id}"
OUTPUT_PATH="${2:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa bundle.id}"
TARGET_BUNDLE_ID="${3:?usage: package_unsigned_ipa.sh path/to/App.app output.ipa bundle.id}"
UPSTREAM_BUNDLE_ID="ph.telegra.Telegraph"

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

# The upstream fake profiles are intentionally used only to let Bazel produce an
# IPA. They cannot represent the independent NagramiX identifier. Rewrite every
# app/extension identifier after signatures and profiles have been removed; the
# user's SideStore installation supplies the real signature.
while IFS= read -r -d '' plist; do
  current_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$plist" 2>/dev/null || true)"
  if [[ "$current_id" == "$UPSTREAM_BUNDLE_ID"* ]]; then
    suffix="${current_id#"$UPSTREAM_BUNDLE_ID"}"
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier ${TARGET_BUNDLE_ID}${suffix}" "$plist"
  fi
done < <(find .nagramix-package/Payload/NagramiX.app -name 'Info.plist' -type f -print0)

/usr/libexec/PlistBuddy -c 'Set :CFBundleDisplayName NagramiX' .nagramix-package/Payload/NagramiX.app/Info.plist

if find .nagramix-package/Payload/NagramiX.app -name 'Info.plist' -type f -print0 \
  | xargs -0 strings \
  | grep -Fq "$UPSTREAM_BUNDLE_ID"; then
  echo "An upstream bundle identifier remains in the unsigned package" >&2
  exit 1
fi

final_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' .nagramix-package/Payload/NagramiX.app/Info.plist)"
test "$final_id" = "$TARGET_BUNDLE_ID" || { echo "Unexpected final bundle id: $final_id" >&2; exit 1; }
(
  cd .nagramix-package
  /usr/bin/zip -qry "../$OUTPUT_PATH" Payload
)
echo "Created unsigned IPA: $OUTPUT_PATH ($final_id)"
