#!/usr/bin/env bash
# Extension C: only the edge (Mac 2) may reach this backend's port. Run on Mac 3 (3001) / Mac 4 (3002).
#   ./isolate_pf.sh 3001
#   EXTRA_ALLOW=$MAC3_IP ./isolate_pf.sh 3002     # also allow the standby edge (Extension E)
# Undo with ./rollback_pf.sh
source "$(dirname "$0")/lib.sh"
PORT="${1:?usage: $0 <backend-port>}"
ALLOW="$MAC2_IP"; [ -n "${EXTRA_ALLOW:-}" ] && ALLOW="$MAC2_IP, $EXTRA_ALLOW"
STATE="$HOME/cn-pf-state"; mkdir -p "$STATE"

step "Rollback copy"
sudo cp -n /etc/pf.conf /etc/pf.conf.rollback          # -n: never overwrite an existing rollback
sudo pfctl -s rules > "$STATE/rules-before.txt" 2>/dev/null
sudo pfctl -s info 2>/dev/null | head -1 | tee "$STATE/status-before.txt"

step "Build /etc/pf.cn.conf (default rules + isolation)"
sudo cp /etc/pf.conf /etc/pf.cn.conf
sudo tee -a /etc/pf.cn.conf >/dev/null <<EOF
# --- CN project isolation: only the edge may reach the backend ---
pass quick on lo0 all
pass in quick proto tcp from { $ALLOW } to any port $PORT
block drop in quick proto tcp from any to any port $PORT
EOF
sudo pfctl -nf /etc/pf.cn.conf                          # syntax check only
sudo pfctl -f /etc/pf.cn.conf
sudo pfctl -e 2>&1 | grep -v "already enabled" || true
step "Active rules for port $PORT"
sudo pfctl -s rules | grep "$PORT"
c_ok "Isolation ON. Test: from Mac 2 curl http://$(my_ip):$PORT/health works; from Mac 1 it times out."
