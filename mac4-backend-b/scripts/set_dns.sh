#!/usr/bin/env bash
# Point THIS Mac's resolver at the team DNS server(s). Your previous DNS settings are saved first.
#   ./set_dns.sh primary   -> Mac 1 only
#   ./set_dns.sh both      -> Mac 1 then backup DNS (Extension A)
#   ./set_dns.sh backup    -> backup only
#   ./set_dns.sh restore   -> put back what this Mac had before (also: reset)
#   ./set_dns.sh show      -> what is in use now
source "$(dirname "$0")/lib.sh"
SAVE="$HOME/.cn-dns-backup"
save_prev() {
  [ -f "$SAVE" ] && return 0
  cur="$(networksetup -getdnsservers "$NET_SERVICE")"
  case "$cur" in *"aren't any"*) echo "empty" > "$SAVE" ;; *) echo "$cur" | tr '\n' ' ' > "$SAVE" ;; esac
  c_info "Saved previous DNS settings: $(cat "$SAVE")"
}
case "${1:-show}" in
  primary) require_ip MAC1_IP; save_prev; sudo networksetup -setdnsservers "$NET_SERVICE" "$MAC1_IP" ;;
  both)    require_ip MAC1_IP; save_prev; sudo networksetup -setdnsservers "$NET_SERVICE" "$MAC1_IP" "$BACKUP_DNS_IP" ;;
  backup)  save_prev; sudo networksetup -setdnsservers "$NET_SERVICE" "$BACKUP_DNS_IP" ;;
  restore|reset)
    if [ -f "$SAVE" ]; then sudo networksetup -setdnsservers "$NET_SERVICE" $(cat "$SAVE"); rm -f "$SAVE"
    else sudo networksetup -setdnsservers "$NET_SERVICE" empty; fi ;;
  show) ;;
  *) echo "usage: $0 primary|both|backup|restore|show"; exit 1 ;;
esac
[ "${1:-show}" != "show" ] && flush_dns
echo "networksetup: $(networksetup -getdnsservers "$NET_SERVICE" | tr '\n' ' ')"
scutil --dns | grep -m4 nameserver
warn_dns_proxy
