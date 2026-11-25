#!/usr/bin/env bash
# Ext E helper (Mac 2): give app.crt + app.key to the STANDBY edge (Mac 3) over the LAN, once, then stop.
# Only STANDBY_EDGE_IP may download; the server exits by itself after both files were served.
source "$(dirname "$0")/lib.sh"
[ -f "$ROOT_DIR/certs/app.crt" ] && [ -f "$ROOT_DIR/certs/app.key" ] || { c_bad "Run ./make_certs.sh first"; exit 1; }
c_info "Serving certs on :8001 ONLY to $STANDBY_EDGE_IP ... (tell Keshav to continue; this stops by itself)"
python3 - "$STANDBY_EDGE_IP" "$ROOT_DIR/certs" <<'PY'
import http.server, sys, os
allowed, d = sys.argv[1], sys.argv[2]
need, got = {"/app.crt", "/app.key"}, set()
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        if s.client_address[0] != allowed or s.path not in need:
            s.send_error(403); return
        data = open(os.path.join(d, s.path[1:]), "rb").read()
        s.send_response(200); s.send_header("Content-Length", str(len(data))); s.end_headers(); s.wfile.write(data)
        got.add(s.path); print("served", s.path, flush=True)
    def log_message(*a): pass
srv = http.server.HTTPServer(("0.0.0.0", 8001), H)
while got != need: srv.handle_request()
print("both files served - done")
PY
