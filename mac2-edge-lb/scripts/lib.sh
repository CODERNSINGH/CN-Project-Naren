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

is_ip()  { [[ "$1" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; }
# warn if a local DNS proxy (Cloudflare WARP / filter app / VPN) hijacks the resolver
warn_dns_proxy() {
  if scutil --dns | grep -q 'nameserver\[[0-9]*\] : 127\.'; then
    c_bad "WARNING: a local DNS proxy is active ($(scutil --dns | grep -m1 -o '127\.[0-9.]*')). Likely Cloudflare WARP / a VPN / filter app."
    c_bad "         It overrides the team DNS. Disconnect it (menu-bar icon -> turn off) before the DNS steps, then re-run set_dns.sh."
  fi
}
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

# require_ip NAME  -> abort if team.env value is not a real IPv4 yet
require_ip() { local v="${!1}"; is_ip "$v" || { c_bad "$1 is '$v' in team.env - get the IP (./scripts/my_ip.sh), run ./setup_team.sh, git pull"; exit 1; }; }

# assert_my_ip EXPECTED_IP  -> warn if this Mac does not own that IP
assert_my_ip() {
  if ! ifconfig | grep -q "inet $1 "; then
    c_bad "This Mac does not have IP $1 (it has: $(my_ip)). Fix team.env or run this on the right Mac."
    exit 1
  fi
}
