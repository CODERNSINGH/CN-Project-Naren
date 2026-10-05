#!/usr/bin/env bash
# Render the nginx config, validate and (re)load it.
#   ./configure_nginx.sh            -> primary edge, X-Edge: mac2   (Mac 2)
#   ./configure_nginx.sh standby    -> standby edge, X-Edge: standby (Mac 3, Extension E)
# Needs certs/app.crt + certs/app.key (made by make_certs.sh on Mac 2; copy to the standby).
source "$(dirname "$0")/lib.sh"
need nginx "brew install nginx"
EDGE_ID="mac2"; [ "${1:-}" = "standby" ] && EDGE_ID="standby"
if [ "$EDGE_ID" = "mac2" ]; then assert_my_ip "$MAC2_IP"; else assert_my_ip "$STANDBY_EDGE_IP"; fi
UPSTREAM_A="# Backend A (Mac 3) not set yet in team.env"; UPSTREAM_B="# Backend B (Mac 4) not set yet in team.env"
is_ip "$MAC3_IP" && UPSTREAM_A="server $MAC3_IP:3001 max_fails=2 fail_timeout=10s;   # Backend A"
is_ip "$MAC4_IP" && UPSTREAM_B="server $MAC4_IP:3002 max_fails=2 fail_timeout=10s;   # Backend B"
is_ip "$MAC3_IP" || is_ip "$MAC4_IP" || { c_bad "No backend IP in team.env"; exit 1; }
is_ip "$MAC4_IP" || c_info "NOTE: MAC4_IP not set -> Backend B left out of the upstream. Re-run this script after ./setup_team.sh + git pull."
CERT="${CERT:-$ROOT_DIR/certs/app.crt}"
KEY="${KEY:-$ROOT_DIR/certs/app.key}"
[ -f "$CERT" ] && [ -f "$KEY" ] || { c_bad "Missing $CERT / $KEY"; exit 1; }

PREFIX="$(brew --prefix)"
LOG_DIR="$PREFIX/var/log/nginx"; RUN_DIR="$PREFIX/var/run"
mkdir -p "$LOG_DIR" "$RUN_DIR" "$ROOT_DIR/generated"
# HTTP/2 syntax depends on the nginx build: >=1.25.1 uses "http2 on;", older uses "listen ... ssl http2;",
# and some builds (e.g. nginx-full) have no http_v2 module at all (HTTP/2 is optional for the project).
HTTP2_LISTEN=""; HTTP2_ON="# http2 not available in this nginx build"
if nginx -V 2>&1 | grep -q http_v2_module; then
  NV="$(nginx -v 2>&1 | sed 's|.*/||')"
  if [ "$(printf '%s\n1.25.1\n' "$NV" | sort -V | head -1)" = "1.25.1" ]; then
    HTTP2_ON="http2 on;"
  else
    HTTP2_LISTEN=" http2"; HTTP2_ON=""
  fi
  c_info "HTTP/2 enabled (nginx $NV)"
else
  c_info "HTTP/2 module missing in this nginx -> serving HTTP/1.1 only (fix: brew install nginx)"
fi
RENDER_VARS="EDGE_ID TEAM UPSTREAM_A UPSTREAM_B HTTP_PORT HTTPS_PORT CERT KEY LOG_DIR RUN_DIR HTTP2_LISTEN HTTP2_ON"
render "$LIB_DIR/nginx.conf.template" > "$ROOT_DIR/generated/nginx.conf"

NGX_CONF="$PREFIX/etc/nginx/nginx.conf"
[ -f "$NGX_CONF" ] && [ ! -f "$NGX_CONF.orig" ] && cp "$NGX_CONF" "$NGX_CONF.orig"
cp "$ROOT_DIR/generated/nginx.conf" "$NGX_CONF"

step "nginx -t"
nginx -t || exit 1
if pgrep -x nginx >/dev/null; then
  step "Reloading"; nginx -s reload
else
  step "Starting";  nginx
fi
sleep 1
lsof -nP -iTCP:"$HTTPS_PORT" -sTCP:LISTEN | head -3
c_ok "Edge '$EDGE_ID' up on :$HTTPS_PORT.  Config copy: $ROOT_DIR/generated/nginx.conf"
echo "Logs: tail -f $LOG_DIR/error.log $LOG_DIR/access.log"
