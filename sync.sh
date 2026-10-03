#!/usr/bin/env bash
# Copies team.env + shared scripts into the four Mac folders and builds dist/*.zip for transfer.
# Run again after EVERY edit of team.env or anything in _shared/.
set -e
cd "$(dirname "$0")"
M1=mac1-dns-client; M2=mac2-edge-lb; M3=mac3-backend-a; M4=mac4-backend-b
for d in $M1 $M2 $M3 $M4; do
  mkdir -p "$d/scripts" "$d/evidence"
  cp team.env "$d/team.env"
  cp _shared/common/* "$d/scripts/"
done
cp _shared/mac2/* "$M2/scripts/"
for pair in "$M3:A:3001" "$M4:B:3002"; do
  IFS=: read -r d id port <<<"$pair"
  mkdir -p "$d/backend"
  cp _shared/backend/* "$d/backend/"
  printf 'BACKEND_ID=%s\nBACKEND_PORT=%s\n' "$id" "$port" > "$d/backend/backend.env"
  chmod +x "$d/backend/run_backend.sh"
done
chmod +x mac*/scripts/*.sh
mkdir -p dist
for d in $M1 $M2 $M3 $M4; do
  rm -f "dist/$d.zip"
  zip -qr "dist/$d.zip" "$d" -x "*/venv/*" "*/certs/*" "*/generated/*" "*/__pycache__/*" "*/.DS_Store"
done
echo "Synced. Transfer these (AirDrop / USB / scp):"; ls -1 dist/*.zip
