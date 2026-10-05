#!/usr/bin/env bash
# Team lead runs ONCE on Narendra's laptop after everyone has run ./scripts/my_ip.sh:
#   ./setup_team.sh <MAC1_IP> <MAC2_IP> <MAC3_IP> <MAC4_IP|pending> [team-name]
# Example: ./setup_team.sh 192.168.1.11 192.168.1.12 192.168.1.13 192.168.1.14 team1
set -e; cd "$(dirname "$0")"
[ $# -ge 4 ] || { sed -n '2,5p' "$0"; exit 1; }
norm() { case "$1" in -|pending|PENDING) echo PENDING ;; *) echo "$1" ;; esac; }
A1=$(norm "$1"); A2=$(norm "$2"); A3=$(norm "$3"); A4=$(norm "$4")
for ip in "$A1" "$A2" "$A3" "$A4"; do [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ || $ip = PENDING ]] || { echo "bad IP: $ip"; exit 1; }; done
GW="$(route -n get default 2>/dev/null | awk '/gateway:/{print $2}')"
for ip in "$A1" "$A2" "$A3" "$A4"; do [ "$ip" = "$GW" ] && { echo "ERROR: $ip is the ROUTER/gateway, not a Mac"; exit 1; }; done
TEAM="${5:-$(awk -F'[= ]' '/^TEAM=/{print $2}' team.env)}"
sed -i '' -E \
  -e "s|^TEAM=[^ ]*|TEAM=$TEAM|" \
  -e "s|^MAC1_IP=[^ ]*|MAC1_IP=$A1|" -e "s|^MAC2_IP=[^ ]*|MAC2_IP=$A2|" \
  -e "s|^MAC3_IP=[^ ]*|MAC3_IP=$A3|" -e "s|^MAC4_IP=[^ ]*|MAC4_IP=$A4|" \
  -e "s|^BACKUP_DNS_IP=[^ ]*|BACKUP_DNS_IP=$A3|" -e "s|^STANDBY_EDGE_IP=[^ ]*|STANDBY_EDGE_IP=$A3|" team.env
echo "--- team.env now:"; grep -E '^[A-Z_0-9]+=' team.env
./sync.sh
echo; echo "Next: git add -A && git commit -m 'set team IPs' && git push   (teammates then: git pull)"
