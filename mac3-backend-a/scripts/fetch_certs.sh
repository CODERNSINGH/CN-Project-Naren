#!/usr/bin/env bash
# Ext E helper (Mac 3 / standby edge): download app.crt + app.key from Mac 2 (Narendra runs ./serve_certs.sh first).
source "$(dirname "$0")/lib.sh"
mkdir -p "$ROOT_DIR/certs"
for f in app.crt app.key; do
  curl -fsS --max-time 10 -o "$ROOT_DIR/certs/$f" "http://$MAC2_IP:8001/$f" || { c_bad "Download of $f failed - is serve_certs.sh running on Mac 2?"; exit 1; }
done
chmod 600 "$ROOT_DIR/certs/app.key"
A="$(openssl x509 -noout -pubkey -in "$ROOT_DIR/certs/app.crt" | md5)"; B="$(openssl pkey -pubout -in "$ROOT_DIR/certs/app.key" | md5)"
[ "$A" = "$B" ] && c_ok "certificate and key match - standby can use them" || { c_bad "cert/key MISMATCH"; exit 1; }
