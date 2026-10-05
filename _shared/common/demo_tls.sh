#!/usr/bin/env bash
# Task E: prove TLS + certificate validation (never uses -k)
source "$(dirname "$0")/lib.sh"

step "curl -v (TLS version, cipher, certificate verify result)"
curl -sv -o /dev/null "$BASE_URL/api/status" 2>&1 | grep -E "Connected to|SSL connection|TLS|subject:|issuer:|SSL certificate verify|ALPN|HTTP/"

step "openssl s_client (chain + 'Verify return code')"
openssl s_client -connect "$APP_HOST:$HTTPS_PORT" -servername "$APP_HOST" </dev/null 2>/dev/null \
  | grep -E "subject=|issuer=|Protocol|Cipher|Verify return code|Verification"

step "Force TLS 1.2 (so the Certificate message is visible in Wireshark)"
curl -sv --tlsv1.2 --tls-max 1.2 -o /dev/null "$BASE_URL/api/status" 2>&1 | grep -E "TLSv1|SSL connection|SSL certificate verify"

step "Certificate SAN (needs the CA file; run on Mac 2 where certs/ exists)"
[ -f "$ROOT_DIR/certs/app.crt" ] && openssl x509 -in "$ROOT_DIR/certs/app.crt" -noout -subject -dates -ext subjectAltName 2>/dev/null \
  || echo "(skipped: certs/app.crt not on this Mac)"
