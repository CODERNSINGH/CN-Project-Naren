#!/usr/bin/env bash
# Install + configure dnsmasq (Task B / Extension A / B / E).
#   ./setup_dnsmasq.sh primary            (Mac 1)
#   ./setup_dnsmasq.sh backup             (Mac 3, Extension A)
# Optional env vars (must be applied to BOTH servers during experiments):
#   TTL=30                 -> use host-record with a 30 s TTL (Extension B)
#   APP_IP=<ip>            -> point app/api at a different IP (failure 2, Ext B, Ext E)
source "$(dirname "$0")/lib.sh"
ROLE="${1:-primary}"
case "$ROLE" in
  primary) LISTEN_IP="$MAC1_IP" ;;
  backup)  LISTEN_IP="$BACKUP_DNS_IP" ;;
  *) echo "usage: $0 primary|backup"; exit 1 ;;
esac
APP_IP="${APP_IP:-$MAC2_IP}"
require_ip MAC2_IP
need brew "install Homebrew from https://brew.sh"
assert_my_ip "$LISTEN_IP"

brew list dnsmasq >/dev/null 2>&1 || brew install dnsmasq
CONF="$(brew --prefix)/etc/dnsmasq.conf"
mkdir -p "$ROOT_DIR/generated"
OUT="$ROOT_DIR/generated/dnsmasq.conf"

{
  echo "# ---- CN project: $ROLE private DNS ($(date)) ----"
  echo "port=53"
  echo "listen-address=$LISTEN_IP,127.0.0.1"
  echo "bind-interfaces"
  echo "# our zone is answered locally and never forwarded; everything else goes upstream"
  echo "local=/${TEAM}.test/"
  echo "server=8.8.8.8"
  echo "server=1.1.1.1"
  if [ -n "${TTL:-}" ]; then
    echo "host-record=$APP_HOST,$APP_IP,$TTL"
    echo "host-record=$API_HOST,$APP_IP,$TTL"
  else
    echo "address=/$APP_HOST/$APP_IP"
    echo "address=/$API_HOST/$APP_IP"
  fi
  echo "log-queries"
  echo "log-facility=/tmp/dnsmasq.log"
} > "$OUT"

[ -f "$CONF" ] && [ ! -f "$CONF.orig" ] && cp "$CONF" "$CONF.orig"
cp "$OUT" "$CONF"
step "Validating config"
dnsmasq --test -C "$CONF"
step "(Re)starting dnsmasq (needs your password)"
sudo brew services restart dnsmasq
sleep 2
step "Listening sockets"
sudo lsof -nP -iUDP:53 | head -5
step "Self-test"
dig +short "$APP_HOST" @"$LISTEN_IP"
dig "$APP_HOST" @"$LISTEN_IP" +noall +answer
c_ok "Config copy saved to $OUT (include it in the configuration bundle)"
