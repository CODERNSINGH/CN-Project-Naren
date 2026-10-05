#!/usr/bin/env bash
# Mac 2 only. Wipes the Mac 2 build so you can redo it from scratch (and screenshot every step).
# Stops nginx, restores the ORIGINAL nginx.conf, deletes certs/, public/, generated/.
source "$(dirname "$0")/lib.sh"
read -r -p "This stops nginx and deletes certs/ public/ generated/ in this folder. Type YES: " a
[ "$a" = "YES" ] || { echo "cancelled"; exit 1; }
nginx -s stop 2>/dev/null && echo "nginx stopped" || echo "nginx was not running"
NGX="$(brew --prefix)/etc/nginx/nginx.conf"
[ -f "$NGX.orig" ] && cp "$NGX.orig" "$NGX" && echo "restored original $NGX"
rm -rf "$ROOT_DIR/certs" "$ROOT_DIR/public" "$ROOT_DIR/generated"
pkill -f "http.server 8000" 2>/dev/null
c_ok "Mac 2 reset. Start again at roadmap step 'Mac 2: make_certs'."
