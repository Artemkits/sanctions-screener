#!/bin/sh
# Deploy or update the app on a Linux server over SSH (Ubuntu 22.04+/Debian 12+).
# Usage: scripts/deploy_vps.sh <ssh-host>        e.g. scripts/deploy_vps.sh vps
# The server pulls the public GitHub repo, installs dependencies into a venv,
# downloads the lists on first run and (re)starts the systemd service on port 8090.
set -e
HOST="$1"
[ -z "$HOST" ] && { echo "usage: $0 <ssh-host>"; exit 1; }
REPO="${REPO:-https://github.com/Artemkits/sanctions-screener.git}"
ssh "$HOST" REPO="$REPO" sh -s <<'REMOTE'
set -e
command -v git >/dev/null || (apt-get update -qq && apt-get install -y -qq git)
python3 -c "import venv, ensurepip" 2>/dev/null || (apt-get update -qq && apt-get install -y -qq python3-venv)
if [ -d /opt/sanctions-screener/.git ]; then
  git -C /opt/sanctions-screener fetch -q && git -C /opt/sanctions-screener reset -q --hard origin/main
else
  git clone -q "$REPO" /opt/sanctions-screener
fi
cd /opt/sanctions-screener
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
mkdir -p data
[ -f data/sanctions.db ] || DATA_DIR=/opt/sanctions-screener/data .venv/bin/python -m app.update
DATA_DIR=/opt/sanctions-screener/data .venv/bin/python -c "from app.matcher import get_index; get_index()"
cp deploy/sanctions-screener.service /etc/systemd/system/sanctions-screener.service
systemctl daemon-reload
systemctl enable -q sanctions-screener
systemctl restart sanctions-screener
sleep 4
systemctl is-active sanctions-screener
curl -s localhost:8090/healthz; echo
REMOTE
