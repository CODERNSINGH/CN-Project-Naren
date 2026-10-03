#!/usr/bin/env bash
# Install the team CA into this Mac's System keychain so curl/browsers trust the edge.
#   ./trust_ca.sh               -> downloads ca.crt from Mac 2 (needs mac2 'serve_ca.sh' running)
#   ./trust_ca.sh /path/ca.crt  -> use a file you copied (AirDrop / scp)
source "$(dirname "$0")/lib.sh"
CA="${1:-$ROOT_DIR/ca.crt}"
if [ -z "${1:-}" ]; then
  c_info "Downloading CA from http://$MAC2_IP:8000/ca.crt"
  curl -fsS -o "$CA" "http://$MAC2_IP:8000/ca.crt" || { c_bad "Download failed - is serve_ca.sh running on Mac 2?"; exit 1; }
fi
step "CA fingerprint (must be identical on every Mac)"
openssl x509 -in "$CA" -noout -subject -fingerprint -sha256
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$CA"
c_ok "CA trusted. Test (no -k!):  curl -sI $BASE_URL/api/status"
echo "Homebrew curl / python ignore the keychain; use:  curl --cacert $CA ..."
