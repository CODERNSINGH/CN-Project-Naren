#!/usr/bin/env bash
# Extension B: watch the SYSTEM resolver cache. Run on a client, then change the record on Mac 1:
#   Mac 1:  TTL=30 APP_IP=<MAC4_IP> ./setup_dnsmasq.sh primary
# Ctrl+C to stop. In a 2nd terminal flush with:  ./set_dns.sh show; sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
source "$(dirname "$0")/lib.sh"
c_info "time | system resolver (cached) | dig direct to Mac 1 (always fresh) | TTL left in dig answer"
while true; do
  SYS="$(dscacheutil -q host -a name "$APP_HOST" | awk '/ip_address/{print $2; exit}')"
  DIG="$(dig +noall +answer "$APP_HOST" @"$MAC1_IP" | awk '{print $2" "$5}' | head -1)"
  printf '%s  system=%-15s  dig(ttl ip)=%s\n' "$(date +%T)" "${SYS:-none}" "$DIG"
  sleep 5
done
