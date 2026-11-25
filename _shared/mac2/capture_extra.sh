#!/usr/bin/env bash
# Mac 2 only: capture the extra Phase 1 evidence that can be produced from the edge laptop itself
# (ping matrix, DNS answers, failure demos 1/4/5, caching headers). Output -> evidence/*.txt
source "$(dirname "$0")/lib.sh"
CA="$ROOT_DIR/public/ca.crt"
cap() { local n="$1"; shift; { echo "# captured $(date '+%F %T') on Mac 2 ($(my_ip))"; echo "\$ $*"; eval "$*"; } 2>&1 | sed $'s/\033\\[[0-9;]*m//g' | tee "$EVID/$n.txt"; echo; }

cap A2-ping-matrix './check_lan.sh'
cap B8-dns-from-mac1 'dig app.team1.test @$MAC1_IP +noall +answer; dig +short api.team1.test @$MAC1_IP'
STARTED=0; pgrep -x nginx >/dev/null || { ./configure_nginx.sh >/dev/null 2>&1; STARTED=1; }
IP="$(dig +short $APP_HOST @$MAC1_IP | head -1)"; IP="${IP:-$MAC2_IP}"
cap X1-wrong-dns 'echo "--- dig to a DNS server that does not exist (expect: timed out)"; dig +time=2 +tries=1 $APP_HOST @${MAC1_IP%.*}.250 | tail -3; echo "--- the real DNS server and the edge are still reachable by IP"; ping -c 2 $MAC1_IP | tail -2; nc -vz -w 3 $MAC2_IP $HTTPS_PORT'
cap X4-both-backends-down 'echo "--- DNS ok:"; dig +short $APP_HOST @$MAC1_IP; echo "--- TLS ok:"; openssl s_client -connect $IP:$HTTPS_PORT -servername $APP_HOST -CAfile "$CA" </dev/null 2>/dev/null | grep -E "subject=|issuer=|Verify return code"; echo "--- HTTP through the edge (both backends are down):"; curl -si --max-time 15 --cacert "$CA" --resolve $APP_HOST:$HTTPS_PORT:$IP $BASE_URL/api/status | head -8; echo "--- nginx error log:"; tail -n 3 "$(brew --prefix)/var/log/nginx/error.log"'
cap X5-wrong-port 'curl -sv --max-time 6 --cacert "$CA" --resolve $APP_HOST:9999:$IP https://$APP_HOST:9999/ 2>&1 | grep -E "Trying|refused|timed out|Failed"; nc -vz -w 3 $IP 9999'
[ $STARTED = 1 ] && nginx -s stop 2>/dev/null

# caching headers: same backend.py the team ran on Mac 3/4, started locally on Mac 2 (the lab backends are off now)
( cd "$ROOT_DIR/../_shared/backend" && BACKEND_ID=A BACKEND_PORT=3901 python3 backend.py >/dev/null 2>&1 ) & BP=$!; sleep 2
cap F1-caching 'echo "--- 1) first request: full 200 with Cache-Control + ETag"; curl -si http://127.0.0.1:3901/api/catalog | sed -n "1,12p"; E=$(curl -sI http://127.0.0.1:3901/api/catalog | tr -d "\r" | awk -F": " "tolower(\$1)==\"etag\"{print \$2}"); echo; echo "--- 2) conditional request with If-None-Match: $E  (expect 304, no body)"; curl -si -H "If-None-Match: $E" http://127.0.0.1:3901/api/catalog | sed -n "1,8p"; echo; echo "--- 3) dynamic endpoint must NOT be cached"; curl -sI http://127.0.0.1:3901/api/status | grep -i -E "HTTP/|cache-control"'
kill $BP 2>/dev/null
