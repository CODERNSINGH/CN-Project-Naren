#!/usr/bin/env bash
# Task E (Mac 2): create a team CA and a server certificate with SANs (OpenSSL "local CA" option).
# Output: certs/ca.crt ca.key app.crt app.key   and   public/ca.crt (safe to share)
source "$(dirname "$0")/lib.sh"
D="$ROOT_DIR/certs"; mkdir -p "$D" "$ROOT_DIR/public"; cd "$D"

step "1. Team CA"
cat > ca.cnf <<EOF
[req]
distinguished_name = dn
x509_extensions    = v3_ca
prompt             = no
[dn]
CN = ${TEAM} Local CA
[v3_ca]
basicConstraints       = critical,CA:TRUE
keyUsage               = critical,keyCertSign,cRLSign
subjectKeyIdentifier   = hash
EOF
openssl genrsa -out ca.key 4096 2>/dev/null
openssl req -x509 -new -nodes -key ca.key -sha256 -days 825 -config ca.cnf -out ca.crt

step "2. Server key + CSR"
openssl genrsa -out app.key 2048 2>/dev/null
openssl req -new -key app.key -subj "/CN=$APP_HOST" -out app.csr

step "3. Sign with SAN (CN alone is not enough for browsers/curl)"
cat > san.ext <<EOF
subjectAltName         = DNS:$APP_HOST,DNS:$API_HOST
basicConstraints       = CA:FALSE
keyUsage               = digitalSignature,keyEncipherment
extendedKeyUsage       = serverAuth
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid
EOF
openssl x509 -req -in app.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out app.crt -days 365 -sha256 -extfile san.ext 2>/dev/null

step "4. Inspect + verify"
openssl x509 -in app.crt -noout -subject -issuer -dates
openssl x509 -in app.crt -noout -text | grep -A1 "Subject Alternative"
openssl verify -CAfile ca.crt app.crt

cp ca.crt "$ROOT_DIR/public/ca.crt"
chmod 600 ca.key app.key
c_ok "Done. Share ONLY public/ca.crt (run ./serve_ca.sh). Standby edge also needs certs/app.crt + app.key."
