#!/usr/bin/env bash
# Task A - collect this Mac's network facts and ping every other Mac.
source "$(dirname "$0")/lib.sh"

IF="$(default_iface)"; IF="${IF:-en0}"
HEXMASK="$(ifconfig "$IF" | awk '/inet /{print $4}')"
MASK="n/a"
if [ -n "$HEXMASK" ]; then
  MASK="$(printf '%d.%d.%d.%d' $((0x${HEXMASK:2:2})) $((0x${HEXMASK:4:2})) $((0x${HEXMASK:6:2})) $((0x${HEXMASK:8:2})))"
fi

step "This Mac (copy into the IP inventory table)"
echo "Interface : $IF"
echo "IPv4      : $(ipconfig getifaddr "$IF")"
echo "Netmask   : $MASK  ($HEXMASK)"
echo "Gateway   : $(netstat -nr | awk '$1=="default"{print $2; exit}')"
echo "MAC addr  : $(ifconfig "$IF" | awk '/ether/{print $2}')"
echo "Hostname  : $(scutil --get LocalHostName 2>/dev/null)"
echo "DNS in use: $(networksetup -getdnsservers "$NET_SERVICE" 2>/dev/null | tr '\n' ' ')"

step "Ping matrix from this Mac"
for pair in "Mac1:$MAC1_IP" "Mac2:$MAC2_IP" "Mac3:$MAC3_IP" "Mac4:$MAC4_IP"; do
  name="${pair%%:*}"; ip="${pair#*:}"
  is_ip "$ip" || { echo "SKIP  $name (IP not set in team.env yet)"; continue; }
  if ping -c 2 -t 4 "$ip" >/dev/null 2>&1; then c_ok "OK    $name $ip"; else c_bad "FAIL  $name $ip"; fi
done
echo
echo "If a ping fails: same Wi-Fi? VPN off? Router 'client/AP isolation' off? (use a phone hotspot)"
