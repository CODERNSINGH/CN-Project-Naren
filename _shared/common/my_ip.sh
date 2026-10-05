#!/usr/bin/env bash
# Run FIRST on every Mac. Standalone (needs nothing else). Prints everything for the IP inventory table.
IF="$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')"; IF="${IF:-en0}"
IP="$(ipconfig getifaddr "$IF" 2>/dev/null)"
HEX="$(ifconfig "$IF" 2>/dev/null | awk '/inet /{print $4}')"
MASK="$(ipconfig getoption "$IF" subnet_mask 2>/dev/null)"
[ -z "$MASK" ] && [ -n "$HEX" ] && MASK="$(printf '%d.%d.%d.%d' $((0x${HEX:2:2})) $((0x${HEX:4:2})) $((0x${HEX:6:2})) $((0x${HEX:8:2})))"
GW="$(route -n get default 2>/dev/null | awk '/gateway:/{print $2}')"
SVC="$(networksetup -listallhardwareports | awk -v d="$IF" '/Hardware Port/{p=substr($0,16)} $0 ~ "Device: "d"$"{print p}')"
echo "================ THIS MAC ================"
echo "Hostname        : $(scutil --get LocalHostName 2>/dev/null)   (user: $(whoami))"
echo "Interface       : $IF   (service name: ${SVC:-unknown}  -> NET_SERVICE in team.env)"
echo "IPv4 address    : ${IP:-NOT CONNECTED}"
echo "Netmask         : ${MASK:-n/a}"
echo "Default gateway : ${GW:-n/a}   <- this is the ROUTER, never use it as a Mac IP"
echo "DHCP server     : $(ipconfig getoption "$IF" server_identifier 2>/dev/null)"
echo "MAC address     : $(ifconfig "$IF" 2>/dev/null | awk '/ether/{print $2}')"
echo "DNS servers     : $(scutil --dns | awk '/nameserver\[/{print $3}' | sort -u | tr '\n' ' ')"
echo "Public IP       : $(curl -s --max-time 4 ifconfig.me 2>/dev/null)"
echo "=========================================="
[ -z "$IP" ] && { echo "Not connected! Join the shared Wi-Fi/hotspot first."; exit 1; }
if scutil --dns | grep -q 'nameserver\[[0-9]*\] : 127\.'; then
  echo "WARNING: DNS is 127.x.x.x -> a local DNS proxy (Cloudflare WARP / VPN / filter app) is ON."
  echo "         Turn it OFF before the DNS steps, otherwise the team DNS server is ignored."
fi
echo "Send this line to the team lead:   <MacN>_IP=$IP"
[ -n "$GW" ] && { echo "--- ping router:"; ping -c 3 "$GW" | tail -2; }
