#!/usr/bin/env bash
# Phase 2 readiness check (read-only). Run on a CLIENT (Mac 1). Shows which extensions are ready to demo.
source "$(dirname "$0")/lib.sh"
ok=0; bad=0
t() { # t "label" command...
  local l="$1"; shift
  if "$@" >/dev/null 2>&1; then c_ok "READY  $l"; ok=$((ok+1)); else c_bad "NOT    $l"; bad=$((bad+1)); fi
}
ans() { dig +short +time=2 +tries=1 "$APP_HOST" @"$1" | head -1; }

step "Ext A - primary + backup DNS (must give the SAME answer)"
P="$(ans "$MAC1_IP")"; B="$(ans "$BACKUP_DNS_IP")"
echo "primary $MAC1_IP -> ${P:-none}   backup $BACKUP_DNS_IP -> ${B:-none}"
t "primary DNS answers"           test -n "$P"
t "backup DNS answers"            test -n "$B"
t "primary == backup"             test "$P" = "$B" -a -n "$P"
t "client lists both resolvers"   bash -c "networksetup -getdnsservers '$NET_SERVICE' | grep -q '$BACKUP_DNS_IP'"

step "Ext B - TTL visible in answers (set TTL=30 on both servers first)"
echo "TTL now: $(dig +noall +answer "$APP_HOST" @"$MAC1_IP" | awk '{print $2; exit}') s"

step "Ext D - failover (needs edge + both backends)"
t "edge answers 200"              bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 '$BASE_URL/api/status')\" = 200 ]"
t "backend A direct"              curl -sf --max-time 4 "http://$MAC3_IP:3001/health"
t "backend B direct"              curl -sf --max-time 4 "http://$MAC4_IP:3002/health"

step "Ext E - primary edge + standby edge"
t "edge Mac 2 sends X-Edge: mac2"      bash -c "curl -sI --max-time 8 --resolve $APP_HOST:$HTTPS_PORT:$MAC2_IP $BASE_URL/api/status | tr -d '\r' | grep -qi '^x-edge: mac2'"
t "standby sends X-Edge: standby"      bash -c "curl -sI --max-time 8 --resolve $APP_HOST:$HTTPS_PORT:$STANDBY_EDGE_IP $BASE_URL/api/status | tr -d '\r' | grep -qi '^x-edge: standby'"

step "Summary"
echo "ready: $ok   not ready: $bad   (Ext C pf is checked on Mac 3/4 with: sudo pfctl -s rules | grep 300)"
[ "$bad" -eq 0 ]
