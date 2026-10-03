#!/usr/bin/env bash
# Extension F - layered troubleshooting runbook. Run on a client; read the first FAIL.
# Order: LAN/IP -> DNS -> TCP -> TLS -> HTTP/app -> backends.
source "$(dirname "$0")/lib.sh"
fail=0
chk() { # chk "label" "hint" command...
  local label="$1" hint="$2"; shift 2
  if "$@" >/dev/null 2>&1; then c_ok "PASS  $label"; else c_bad "FAIL  $label   -> suspect: $hint"; fail=1; fi
}
step "0. LAN / IP layer"
chk "ping gateway"      "Wi-Fi, VPN, wrong network"             ping -c 2 -t 3 "$(netstat -nr | awk '$1=="default"{print $2; exit}')"
chk "ping edge Mac 2"   "edge Mac off/wrong net, firewall ICMP" ping -c 2 -t 3 "$MAC2_IP"

step "1. DNS layer"
echo "resolver in use:"; scutil --dns | grep -m2 nameserver
chk "dig answers (NOERROR)"        "wrong client resolver / dnsmasq down"  bash -c "dig +time=2 +tries=1 $APP_HOST | grep -q 'status: NOERROR'"
GOT="$(dig +short +time=2 +tries=1 "$APP_HOST" | head -1)"
echo "dig says $APP_HOST = ${GOT:-<nothing>}   (expected $MAC2_IP)"
[ "$GOT" = "$MAC2_IP" ] && c_ok "PASS  record points to the edge" || { c_bad "FAIL  wrong/missing record -> check dnsmasq.conf, stale cache (flush)"; fail=1; }
chk "system resolver agrees"       "stale cache: flush mDNSResponder"       bash -c "dscacheutil -q host -a name $APP_HOST | grep -q $MAC2_IP"

step "2. TCP layer"
chk "edge port $HTTPS_PORT open"   "nginx down, wrong port, pf/firewall, wrong bind" nc -z -w 3 "$MAC2_IP" "$HTTPS_PORT"

step "3. TLS layer"
VR="$(openssl s_client -connect "$MAC2_IP:$HTTPS_PORT" -servername "$APP_HOST" </dev/null 2>/dev/null | grep -i 'Verify return code')"
echo "$VR"
echo "$VR" | grep -q "(ok)" && c_ok "PASS  certificate verifies" || { c_bad "FAIL  expired cert / SAN mismatch / CA not trusted / wrong cert-key pair"; fail=1; }

step "4. HTTP / application layer (through the edge)"
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 12 "$BASE_URL/api/status")"
echo "HTTP status: $CODE"
[ "$CODE" = "200" ] && c_ok "PASS  200 via edge" || { c_bad "FAIL  502/504 = upstream down or wrong upstream IP/port; 404 = nginx location/server_name"; fail=1; }

step "5. Backends directly (may be blocked on purpose by pf - Extension C)"
chk "Backend A $MAC3_IP:3001" "app stopped / bound to 127.0.0.1 / pf rule" curl -s --max-time 4 "http://$MAC3_IP:3001/health"
chk "Backend B $MAC4_IP:3002" "app stopped / bound to 127.0.0.1 / pf rule" curl -s --max-time 4 "http://$MAC4_IP:3002/health"

step "6. Logs"
echo "Mac 2: tail -f \$(brew --prefix)/var/log/nginx/error.log      Mac 1: tail /tmp/dnsmasq.log"
exit $fail
