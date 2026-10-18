#!/bin/sh
# Push the current commit to a Hugging Face Space (Docker SDK).
# Usage: scripts/deploy_hf.sh <hf-username> [space-name]
# Requires: `pip install huggingface_hub` and `huggingface-cli login` (token with write access).
set -e
USER="$1"; SPACE="${2:-sanctions-screener}"
[ -z "$USER" ] && { echo "usage: $0 <hf-username> [space-name]"; exit 1; }
TMP=$(mktemp -d)
git archive HEAD | tar -x -C "$TMP"
# Spaces read their configuration from a YAML header in README.md
{ printf -- '---\ntitle: Sanctions Screener\ncolorFrom: blue\ncolorTo: gray\nsdk: docker\napp_port: 7860\npinned: false\n---\n\n'; cat "$TMP/README.md"; } > "$TMP/README.hf" && mv "$TMP/README.hf" "$TMP/README.md"
rm -rf "$TMP/docs"   # screenshots are not needed in the Space (binary files need git-lfs there)
huggingface-cli repo create "$SPACE" --type space --space_sdk docker -y 2>/dev/null || true
huggingface-cli upload "$USER/$SPACE" "$TMP" . --repo-type space --commit-message "Deploy $(git rev-parse --short HEAD)"
rm -rf "$TMP"
echo "Deployed: https://huggingface.co/spaces/$USER/$SPACE  (app: https://$USER-$SPACE.hf.space)"
