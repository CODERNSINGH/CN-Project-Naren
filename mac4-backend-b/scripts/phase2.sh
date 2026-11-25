#!/usr/bin/env bash
# PHASE 2 - one command per teammate.   Run inside YOUR Mac's folder:
#     ./scripts/phase2.sh          -> walks through ALL your Phase 2 tasks (stages 0..6)
#     ./scripts/phase2.sh 4        -> only stage 4 (re-do one stage)
# It detects who you are from your IP, runs the commands, saves output to evidence/NAME.txt
# and takes the screenshot evidence/NAME.png by itself. Yellow ">>>" lines = wait for a teammate.
#
# Stages (same numbers for everybody):
#   0 pre-flight   1 Ext A backup DNS   2 Ext D failover   3 Ext B TTL
#   4 Ext C pf isolation   5 Ext E standby edge + DNS cutover   6 Ext F troubleshooting
source "$(dirname "$0")/lib.sh"
D="$(cd "$(dirname "$0")" && pwd)"; cd "$D"

ME=""
has_ip "$MAC1_IP" && ME=mohan
has_ip "$MAC2_IP" && ME=narendra
has_ip "$MAC3_IP" && ME=keshav
has_ip "$MAC4_IP" && ME=mayank
[ -n "$ME" ] || { c_bad "This Mac's IP ($(my_ip)) is not in team.env. git pull, or fix team.env."; exit 1; }

TITLE_0="Pre-flight check"; TITLE_1="Ext A - Backup DNS"; TITLE_2="Ext D - HA failover"; TITLE_3="Ext B - TTL"
TITLE_4="Ext C - pf isolation"; TITLE_5="Ext E - Standby edge + DNS cutover"; TITLE_6="Ext F - Troubleshooting"
banner() { local t="TITLE_$1"; printf '\n\033[1;35m######## STAGE %s: %s   (you are %s) ########\033[0m\n' "$1" "${!t}" "$ME"; }
idle()   { c_info "Nothing for YOU in this stage. Watch your teammates, answer if they ask. (Enter = next)"; read -r _; }
sudo -v   # ask the password once up front

# ============================ STAGE 0 : PRE-FLIGHT ============================
pre_common() {
  step "Pre-flight for $ME"
  has_ip "$(eval echo \$MAC${1}_IP)" && c_ok "IP matches team.env" || c_bad "IP mismatch"
  for c in dig curl nc openssl; do command -v $c >/dev/null && c_ok "have $c" || c_bad "MISSING $c"; done
  scutil --dns | grep -q 'nameserver\[[0-9]*\] : 127\.' && warn_dns_proxy
  T="$EVID/.shot-test.png"; screencapture -x "$T" 2>/dev/null
  if [ -s "$T" ] && [ "$(stat -f%z "$T")" -gt 60000 ]; then c_ok "screenshots work"; else
    c_bad "Screenshots may be blank. System Settings > Privacy & Security > Screen Recording > enable Terminal (restart Terminal)."; fi
  rm -f "$T"
}
mohan_0()    { pre_common 1; "$D/phase2_check.sh" || c_info "(NOT-ready lines are normal before stages 1/5)"; }
narendra_0() { pre_common 2; pgrep -x nginx >/dev/null && c_ok "nginx running" || c_bad "nginx NOT running -> ./scripts/configure_nginx.sh"
               [ -f "$ROOT_DIR/certs/app.crt" ] && c_ok "certs present" || c_bad "no certs -> ./scripts/make_certs.sh"; }
keshav_0()   { pre_common 3; lsof -nP -iTCP:3001 -sTCP:LISTEN >/dev/null && c_ok "Backend A listening" || c_bad "Backend A NOT running -> new terminal: ./backend/run_backend.sh"
               command -v nginx >/dev/null && c_ok "nginx installed" || c_info "nginx missing (stage 5 installs it)"
               command -v dnsmasq >/dev/null && c_ok "dnsmasq installed" || c_info "dnsmasq missing (stage 1 installs it)"; }
mayank_0()   { pre_common 4; lsof -nP -iTCP:3002 -sTCP:LISTEN >/dev/null && c_ok "Backend B listening" || c_bad "Backend B NOT running -> new terminal: ./backend/run_backend.sh"; }

# ============================ STAGE 1 : EXT A ============================
keshav_1() {
  ./setup_dnsmasq.sh backup
  runc EA1-backup-dns 'dig +short $APP_HOST @$BACKUP_DNS_IP; dig $APP_HOST @$BACKUP_DNS_IP +noall +answer; sudo lsof -nP -iUDP:53 | head -3'
  shot EA1-backup-dns
  c_ok "NOW TELL THE TEAM:  'backup DNS is up'"
  pause "Mohan runs the failover test. Continue when he says 'stage 1 done'."
}
mohan_1() {
  pause "WAIT until KESHAV says 'backup DNS is up'."
  runc EA0-both-answer 'echo primary:; dig +short $APP_HOST @$MAC1_IP; echo backup:; dig +short $APP_HOST @$BACKUP_DNS_IP'
  ./set_dns.sh both
  step "Stopping PRIMARY dnsmasq (Mac 1)"; sudo brew services stop dnsmasq; sleep 2; flush_dns
  runc EA2-failover 'echo "--- primary (expect: no servers could be reached)"; dig +tries=1 +time=2 $APP_HOST @$MAC1_IP | tail -3; echo "--- backup (expect: $MAC2_IP)"; dig +short $APP_HOST @$BACKUP_DNS_IP; echo "--- full request still works through fallback (time it):"; time curl -sI --max-time 15 $BASE_URL/ | head -1'
  shot EA2-failover
  sudo brew services start dnsmasq; sleep 2; c_ok "primary dnsmasq started again"
  c_ok "NOW TELL THE TEAM:  'stage 1 done'"
}

# ============================ STAGE 2 : EXT D ============================
keshav_2() {
  pause "Mohan is ready. Enter = STOP Backend A."
  pkill -f "python backend.py"; sleep 1
  runc ED0-A-stopped 'lsof -nP -iTCP:3001 -sTCP:LISTEN || echo "port 3001 closed -> Backend A is DOWN"'
  shot ED0-A-stopped
  c_ok "TELL MOHAN: 'A is stopped'"
  pause "Mohan finished the 'all B' run. Enter = START Backend A again."
  ( cd "$ROOT_DIR/backend" && nohup ./run_backend.sh > /tmp/backendA.log 2>&1 & ); sleep 5
  runc ED0-A-restarted 'curl -s http://$MAC3_IP:3001/health'
  c_ok "TELL MOHAN: 'A is back' (he waits 15 s for fail_timeout)"
}
mohan_2() {
  pause "WAIT for KESHAV: 'A is stopped'."
  runc ED1-failover './demo_lb.sh'; shot ED1-failover
  c_ok "TELL KESHAV: 'restart A'  and  NARENDRA: 'check access log after the recovery run'"
  pause "WAIT for KESHAV: 'A is back'."
  step "Waiting 15 s (fail_timeout=10s)"; sleep 15
  runc ED2-recovery './demo_lb.sh'; shot ED2-recovery
  c_ok "TELL NARENDRA: 'recovery run done - capture the access log now'"
}
narendra_2() {
  pause "WAIT for MOHAN: 'recovery run done'."
  runc ED3-access-log 'tail -n 24 "$(brew --prefix)/var/log/nginx/access.log"'
  shot ED3-access-log
}

# ============================ STAGE 3 : EXT B ============================
keshav_3() {
  pause "Enter = set TTL=30 on the BACKUP DNS."
  TTL=30 ./setup_dnsmasq.sh backup; c_ok "TELL MOHAN: 'TTL set on backup'"
  pause "Mohan finished the TTL experiment. Enter = restore backup to normal."
  ./setup_dnsmasq.sh backup
}
mohan_3() {
  pause "WAIT for KESHAV: 'TTL set on backup'.  Keep this window visible for ~80 s afterwards."
  TTL=30 ./setup_dnsmasq.sh primary >/dev/null; flush_dns
  ./demo_ttl.sh > "$EVID/EB-ttl-timeline.txt" 2>&1 & TP=$!
  c_info "recording timeline (do not touch anything, ~75 s)..."
  sleep 15; c_info "t+15s  changing the DNS record -> Mac 4 IP (old answer should persist <= 30 s)"
  APP_IP=$MAC4_IP TTL=30 ./setup_dnsmasq.sh primary >/dev/null 2>&1
  sleep 40;  c_info "t+55s  flushing the client cache (change should show instantly)"; flush_dns
  sleep 15; kill $TP 2>/dev/null
  echo; cat "$EVID/EB-ttl-timeline.txt"; shot EB-ttl-timeline
  step "Restoring the normal record"; ./setup_dnsmasq.sh primary >/dev/null; flush_dns
  c_ok "TELL KESHAV: 'TTL experiment done'"
}

# ============================ STAGE 4 : EXT C ============================
keshav_4() {
  pause "Enter = pf ISOLATION ON for port 3001 (only Mac 2 may connect)."
  runc EC1-pf-on-mac3 './isolate_pf.sh 3001'; shot EC1-pf-on-mac3
  c_ok "TELL NARENDRA + MOHAN: 'pf is on (Mac 3)'"
  pause "Narendra AND Mohan finished testing. Enter = ROLLBACK pf."
  runc EC5-rollback-ok-mac3 './rollback_pf.sh'; shot EC5-rollback-ok-mac3
}
mayank_4() {
  pause "Enter = pf ISOLATION ON for port 3002 (only Mac 2 may connect)."
  runc EC2-pf-on-mac4 './isolate_pf.sh 3002'; shot EC2-pf-on-mac4
  c_ok "TELL NARENDRA + MOHAN: 'pf is on (Mac 4)'"
  pause "Narendra AND Mohan finished testing. Enter = ROLLBACK pf."
  runc EC5-rollback-ok-mac4 './rollback_pf.sh'; shot EC5-rollback-ok-mac4
}
narendra_4() {
  pause "WAIT for KESHAV *and* MAYANK: 'pf is on'."
  runc EC3-edge-allowed 'echo "--- from the EDGE (expect 200)"; curl -i -m 5 http://$MAC3_IP:3001/health; echo; curl -i -m 5 http://$MAC4_IP:3002/health'
  shot EC3-edge-allowed; c_ok "TELL MOHAN: 'edge test done - your turn'"
}
mohan_4() {
  pause "WAIT for KESHAV + MAYANK ('pf is on') and NARENDRA ('edge test done')."
  runc EC4-client-blocked 'echo "--- direct to A (expect timeout)"; curl -m 5 -i http://$MAC3_IP:3001/health; echo "--- direct to B (expect timeout)"; curl -m 5 -i http://$MAC4_IP:3002/health; echo "--- nc A"; nc -vz -w 3 $MAC3_IP 3001; echo "--- via the edge (expect 200 JSON)"; curl -s $BASE_URL/api/status'
  shot EC4-client-blocked
  c_ok "TELL KESHAV + MAYANK: 'rollback pf now'"
}

# ============================ STAGE 5 : EXT E ============================
narendra_5() {
  pause "Enter = serve the certs to Keshav (only his IP, stops by itself). Tell him to continue."
  ./serve_certs.sh
  c_ok "certs delivered. Wait for 'standby up' and then watch Mohan's cutover."
}
keshav_5() {
  command -v nginx >/dev/null || brew install nginx
  [ -f "$ROOT_DIR/certs/app.crt" ] || { pause "NARENDRA must run stage 5 first (serving certs). Enter = download certs."; ./fetch_certs.sh || exit 1; }
  ./configure_nginx.sh standby
  runc EE1-standby 'curl -sI --resolve $APP_HOST:$HTTPS_PORT:$STANDBY_EDGE_IP $BASE_URL/api/status | head -8; lsof -nP -iTCP:$HTTPS_PORT -sTCP:LISTEN | head -3'
  shot EE1-standby
  c_ok "TELL MOHAN: 'standby up'"
  pause "Mohan finished the cutover test. (standby keeps running; Enter = done)"
}
mohan_5() {
  pause "WAIT for KESHAV: 'standby up'."
  runc EE0-standby-direct 'curl -sI --resolve $APP_HOST:$HTTPS_PORT:$STANDBY_EDGE_IP $BASE_URL/api/status | grep -i -E "HTTP/|x-edge|x-backend"'
  TTL=30 ./setup_dnsmasq.sh primary >/dev/null; flush_dns
  ./demo_edge.sh > "$EVID/EE2-cutover.txt" 2>&1 & TP=$!
  c_info "recording edge timeline (~70 s, do not touch)..."
  sleep 15; c_info "t+15s  DNS cutover: app.team1.test -> STANDBY ($STANDBY_EDGE_IP)"
  APP_IP=$STANDBY_EDGE_IP TTL=30 ./setup_dnsmasq.sh primary >/dev/null 2>&1
  sleep 55; kill $TP 2>/dev/null
  echo; cat "$EVID/EE2-cutover.txt"; shot EE2-cutover
  step "Restoring DNS to Mac 2"; ./setup_dnsmasq.sh primary >/dev/null; flush_dns
  c_ok "TELL KESHAV: 'cutover done'"
}

# ============================ STAGE 6 : EXT F ============================
mohan_6() {
  runc EF1-diagnose-ok './diagnose.sh'; shot EF1-diagnose-ok
  c_ok "TELL NARENDRA: 'EF1 captured - break something'"
  pause "WAIT for NARENDRA: 'fault injected'."
  runc EF2-diagnose-fault './diagnose.sh'; shot EF2-diagnose-fault
  c_info "WRITE DOWN: which layer failed FIRST + the fix (for the report)."
  c_ok "TELL NARENDRA: 'EF2 captured - fix it'"
  pause "WAIT for NARENDRA: 'fixed'."
  runc EF3-final-check './diagnose.sh; ./phase2_check.sh'; shot EF3-final-check
}
narendra_6() {
  pause "WAIT for MOHAN: 'EF1 captured'. Enter = BREAK the edge (stop nginx)."
  nginx -s stop; sleep 1
  runc EF0-fault 'pgrep -x nginx || echo "nginx is STOPPED (fault injected)"'
  c_ok "TELL MOHAN: 'fault injected'"
  pause "WAIT for MOHAN: 'EF2 captured'. Enter = FIX (start nginx again)."
  ./configure_nginx.sh; c_ok "TELL MOHAN: 'fixed'"
}

# ============================ DISPATCH ============================
STAGES="${1:-0 1 2 3 4 5 6}"
for s in $STAGES; do
  banner "$s"
  if declare -F "${ME}_$s" >/dev/null; then "${ME}_$s"; else idle; fi
done
echo
c_ok "All your stages are done. Next:  ./scripts/submit_evidence.sh"
