#!/bin/sh
# Push the current commit to a Hugging Face Space (Docker SDK).
# Usage: scripts/deploy_hf.sh <hf-username> [space-name]
# Requires the `hf` CLI (pip install "huggingface_hub[cli]") and `hf auth login` with a write token.
set -e
USER="$1"; SPACE="${2:-sanctions-screener}"
[ -z "$USER" ] && { echo "usage: $0 <hf-username> [space-name]"; exit 1; }
HF="${HF:-hf}"
TMP=$(mktemp -d)
git archive HEAD | tar -x -C "$TMP"
# Spaces read their configuration from a YAML header in README.md
{ printf -- '---\ntitle: Sanctions Screener\ncolorFrom: blue\ncolorTo: gray\nsdk: docker\napp_port: 7860\npinned: false\nshort_description: Transliteration-aware sanctions screening (EU, UN, OFAC, PL, UK)\n---\n\n'; cat "$TMP/README.md"; } > "$TMP/README.hf" && mv "$TMP/README.hf" "$TMP/README.md"
"$HF" repos create "$USER/$SPACE" --type space --sdk docker --public --exist-ok
"$HF" upload "$USER/$SPACE" "$TMP" . --repo-type space --commit-message "Deploy $(git rev-parse --short HEAD)"
rm -rf "$TMP"
echo "Space: https://huggingface.co/spaces/$USER/$SPACE"
echo "App:   https://$(echo "$USER-$SPACE" | tr '[:upper:]_.' '[:lower:]--').hf.space"
