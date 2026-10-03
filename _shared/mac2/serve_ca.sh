#!/usr/bin/env bash
# Serve ONLY the public CA certificate on :8000 so other Macs can run ./trust_ca.sh. Ctrl+C when done.
source "$(dirname "$0")/lib.sh"
[ -f "$ROOT_DIR/public/ca.crt" ] || { c_bad "Run ./make_certs.sh first"; exit 1; }
c_info "Serving http://$MAC2_IP:8000/ca.crt  (public cert only - private keys are NOT in this folder)"
cd "$ROOT_DIR/public" && exec python3 -m http.server 8000 --bind 0.0.0.0
