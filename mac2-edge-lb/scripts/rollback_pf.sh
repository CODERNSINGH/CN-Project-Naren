#!/usr/bin/env bash
# Extension C: restore the original firewall configuration.
source "$(dirname "$0")/lib.sh"
STATE="$HOME/cn-pf-state"
[ -f /etc/pf.conf.rollback ] || { c_bad "No /etc/pf.conf.rollback - nothing to restore"; exit 1; }
sudo pfctl -f /etc/pf.conf.rollback
if grep -qi disabled "$STATE/status-before.txt" 2>/dev/null; then sudo pfctl -d; echo "pf was disabled before -> disabled again"; fi
sudo rm -f /etc/pf.cn.conf
sudo pfctl -s rules 2>/dev/null | diff - "$STATE/rules-before.txt" && c_ok "rollback OK (rules identical to before)"
