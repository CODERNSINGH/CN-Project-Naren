#!/usr/bin/env bash
# Shared helpers. Every script starts with:  source "$(dirname "$0")/lib.sh"
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$LIB_DIR/.." && pwd)"
if [ ! -f "$ROOT_DIR/team.env" ]; then
  echo "ERROR: $ROOT_DIR/team.env not found" >&2; exit 1
fi
set -a; . "$ROOT_DIR/team.env"; set +a

APP_HOST="app.${TEAM}.test"
API_HOST="api.${TEAM}.test"
HTTPS_PORT="${EDGE_HTTPS_PORT:-8443}"
HTTP_PORT="${EDGE_HTTP_PORT:-8080}"
BASE_URL="https://${APP_HOST}:${HTTPS_PORT}"
NET_SERVICE="${NET_SERVICE:-Wi-Fi}"

c_ok()   { printf '\033[32m%s\033[0m\n' "$*"; }
c_bad()  { printf '\033[31m%s\033[0m\n' "$*"; }
c_info() { printf '\033[36m%s\033[0m\n' "$*"; }
step()   { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
need()   { command -v "$1" >/dev/null 2>&1 || { c_bad "Missing command: $1  ($2)"; exit 1; }; }
my_ip()  { ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null; }
default_iface() { route -n get default 2>/dev/null | awk '/interface:/{print $2}'; }
flush_dns() { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; }

# render TEMPLATE  -> stdout, replacing @@VAR@@ for every name in $RENDER_VARS
render() {
  local f="$1" v; local args=()
  for v in $RENDER_VARS; do args+=(-e "s|@@${v}@@|${!v}|g"); done
  sed "${args[@]}" "$f"
}

# assert_my_ip EXPECTED_IP  -> warn if this Mac does not own that IP
assert_my_ip() {
  if ! ifconfig | grep -q "inet $1 "; then
    c_bad "This Mac does not have IP $1 (it has: $(my_ip)). Fix team.env or run this on the right Mac."
    exit 1
  fi
}
