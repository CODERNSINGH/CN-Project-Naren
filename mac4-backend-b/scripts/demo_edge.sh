#!/usr/bin/env bash
# Extension E: watch which EDGE and which BACKEND answers over time while DNS is cut over.
source "$(dirname "$0")/lib.sh"
c_info "time | edge | backend | resolved IP  (Ctrl+C to stop)"
while true; do
  H="$(curl -s -D - -o /dev/null --max-time 6 "$BASE_URL/api/status" | tr -d '\r')"
  E="$(echo "$H" | awk 'tolower($1)=="x-edge:"{print $2}')"
  B="$(echo "$H" | awk 'tolower($1)=="x-backend:"{print $2}')"
  IP="$(dscacheutil -q host -a name "$APP_HOST" | awk '/ip_address/{print $2; exit}')"
  printf '%s  edge=%-8s backend=%-2s ip=%s\n' "$(date +%T)" "${E:-?}" "${B:-?}" "${IP:-?}"
  sleep 5
done
