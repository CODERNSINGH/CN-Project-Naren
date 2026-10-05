#!/usr/bin/env bash
# Task F / demo step 7: Cache-Control, ETag, 304 conditional request, HTTP/1.1 vs HTTP/2
source "$(dirname "$0")/lib.sh"
URL="$BASE_URL/api/catalog"

step "1. Headers (curl -I)  -> look for Cache-Control + ETag"
curl -sI "$URL"

step "2. Dynamic endpoint uses no-store"
curl -sI "$BASE_URL/api/status" | grep -i -E "HTTP/|cache-control"

step "3. Conditional request with If-None-Match -> expect 304 Not Modified"
ETAG="$(curl -sI "$URL" | tr -d '\r' | awk -F': ' 'tolower($1)=="etag"{print $2}')"
echo "ETag = $ETAG"
curl -sI -H "If-None-Match: $ETAG" "$URL"

step "4. Protocol versions"
echo -n "HTTP/1.1 -> "; curl -s --http1.1 -o /dev/null -w '%{http_version}\n' "$URL"
echo -n "HTTP/2   -> "; curl -s --http2   -o /dev/null -w '%{http_version}\n' "$URL"

echo
c_info "Browser cache-hit demo: open $URL in Chrome > DevTools > Network. Reload within 60 s -> '(memory/disk cache)'."
c_info "Cmd+Shift+R (hard reload) bypasses the cache -> full 200."
