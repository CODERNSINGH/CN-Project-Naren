#!/usr/bin/env bash
# Demo step 5 / Task D / Ext D: repeated requests -> X-Backend alternates A,B,A,B
source "$(dirname "$0")/lib.sh"
N="${1:-6}"
c_info "GET $BASE_URL/api/status  x$N   (no -k: certificate is validated)"
for i in $(seq 1 "$N"); do
  curl -s -D - -o /dev/null --max-time 12 "$BASE_URL/api/status" \
    | tr -d '\r' | awk -v n="$i" 'NR==1{s=$0} tolower($1)=="x-backend:"{b=$2} tolower($1)=="x-edge:"{e=$2} END{printf "%2d  %-18s X-Backend: %-3s X-Edge: %s\n", n, s, b, e}'
done
