#!/usr/bin/env bash
# Phase 1 required failure demonstrations. Run on the CLIENT Mac (Mac 1).
#   ./failures.sh 1   wrong DNS server        (script does the break + restore)
#   ./failures.sh 2   DNS record -> wrong IP  (first: on Mac 1 run  APP_IP=$MAC4_IP ./setup_dnsmasq.sh primary)
#   ./failures.sh 3   one backend stopped     (first: Ctrl+C Backend A on Mac 3)
#   ./failures.sh 4   both backends stopped   (first: stop A and B)
#   ./failures.sh 5   wrong destination port
source "$(dirname "$0")/lib.sh"
case "${1:-}" in
1)
  BAD="${MAC1_IP%.*}.250"
  step "Break: client DNS -> $BAD (nobody there)"
  sudo networksetup -setdnsservers "$NET_SERVICE" "$BAD"; flush_dns
  echo "--- dig (expect: timed out)";            dig +time=2 +tries=1 "$APP_HOST"
  echo "--- ping the edge by IP (expect: works)"; ping -c 3 "$MAC2_IP"
  echo "--- HTTPS by IP, name pinned manually (works => DNS and IP are independent layers)"
  curl -sI --max-time 6 --resolve "$APP_HOST:$HTTPS_PORT:$MAC2_IP" "$BASE_URL/api/status" | head -3
  read -r -p "Press Enter to RESTORE DNS to Mac 1 ..." _
  "$(dirname "$0")/set_dns.sh" primary ;;
2)
  step "Observe: resolution succeeds but points to the wrong host"
  flush_dns
  dig +short "$APP_HOST"
  curl -sv --max-time 8 "$BASE_URL/api/status" 2>&1 | grep -E "Trying|Connected|refused|timed out|SSL|HTTP/|subject"
  c_info "RESTORE on Mac 1:  ./setup_dnsmasq.sh primary   (then flush client cache)" ;;
3)
  step "Observe: only one backend alive -> all answers from the survivor"
  for i in $(seq 1 6); do
    curl -s -D - -o /dev/null --max-time 12 "$BASE_URL/api/status" | tr -d '\r' | grep -i -E "^HTTP/|x-backend" | tr '\n' ' '; echo
  done ;;
4)
  step "Observe: DNS + TCP + TLS fine, upstream dead -> 502"
  dig +short "$APP_HOST"
  openssl s_client -connect "$APP_HOST:$HTTPS_PORT" -servername "$APP_HOST" </dev/null 2>/dev/null | grep -i "verify return\|Verification"
  curl -si --max-time 15 "$BASE_URL/api/status" | head -12 ;;
5)
  step "Observe: host reachable, port closed"
  ping -c 3 "$APP_HOST"
  curl -sv --max-time 6 "https://$APP_HOST:9999/" 2>&1 | grep -E "Trying|refused|timed out|Failed"
  nc -vz -w 3 "$MAC2_IP" 9999
  c_info "Wireshark filter: tcp.port==9999  -> SYN then RST,ACK" ;;
*) sed -n '2,8p' "$0"; exit 1 ;;
esac
