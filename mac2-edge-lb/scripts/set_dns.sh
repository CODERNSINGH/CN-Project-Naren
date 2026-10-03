#!/usr/bin/env bash
# Point THIS Mac's resolver at the team DNS server(s).
#   ./set_dns.sh primary   -> Mac 1 only
#   ./set_dns.sh both      -> Mac 1 then backup DNS (Extension A)
#   ./set_dns.sh backup    -> backup only
#   ./set_dns.sh reset     -> back to DHCP/automatic
#   ./set_dns.sh show      -> what is in use now
source "$(dirname "$0")/lib.sh"
case "${1:-show}" in
  primary) sudo networksetup -setdnsservers "$NET_SERVICE" "$MAC1_IP" ;;
  both)    sudo networksetup -setdnsservers "$NET_SERVICE" "$MAC1_IP" "$BACKUP_DNS_IP" ;;
  backup)  sudo networksetup -setdnsservers "$NET_SERVICE" "$BACKUP_DNS_IP" ;;
  reset)   sudo networksetup -setdnsservers "$NET_SERVICE" empty ;;
  show)    ;;
  *) echo "usage: $0 primary|both|backup|reset|show"; exit 1 ;;
esac
[ "${1:-show}" != "show" ] && flush_dns
echo "networksetup: $(networksetup -getdnsservers "$NET_SERVICE" | tr '\n' ' ')"
scutil --dns | grep -m4 nameserver
