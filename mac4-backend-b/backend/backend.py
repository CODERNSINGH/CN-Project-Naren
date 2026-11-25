#!/usr/bin/env python3
"""Minimal REST backend for the CN project. The network is the project, not the app."""
import os, time, hashlib, threading
from flask import Flask, jsonify, request, make_response

ID = os.environ.get("BACKEND_ID", "A")                 # "A" or "B"
PORT = int(os.environ.get("BACKEND_PORT", "3001"))     # 3001 (A) / 3002 (B)
STARTED = time.time()

app = Flask(__name__)

_count = 0                                             # requests served since start
_lock = threading.Lock()


def client_info():
    """Who is talking to us: the TCP peer, plus what the edge (nginx) forwarded."""
    return {
        "peer": request.remote_addr,                   # Mac 2 / standby edge when proxied
        "real_ip": request.headers.get("X-Real-IP"),   # original client, set by nginx
        "forwarded_for": request.headers.get("X-Forwarded-For"),
        "forwarded_proto": request.headers.get("X-Forwarded-Proto"),  # "https" via edge
        "host": request.host,
    }


@app.before_request
def start_timer():
    request._t0 = time.perf_counter()


@app.after_request
def add_backend_header(resp):
    global _count
    with _lock:
        _count += 1
    ms = (time.perf_counter() - getattr(request, "_t0", time.perf_counter())) * 1000
    resp.headers["X-Backend"] = ID                     # proves which backend answered
    resp.headers["X-Response-Time-ms"] = "%.1f" % ms
    # One log line per request: shows direct (Mac 1 -> :3001) vs via-edge traffic,
    # which is what the isolation (Ext C) and failover (Ext D) demos need to show.
    info = client_info()
    via = "edge" if info["real_ip"] else "direct"
    print("[%s] backend=%s %s %s -> %d peer=%s client=%s via=%s %.1fms" % (
        time.strftime("%H:%M:%S"), ID, request.method, request.path, resp.status_code,
        info["peer"], info["real_ip"] or info["peer"], via, ms), flush=True)
    return resp


@app.get("/")
def index():
    return jsonify(message="Backend %s is running" % ID, port=PORT)


@app.get("/api/status")
def status():
    resp = jsonify(backend=ID, status="ok", time=int(time.time()))
    resp.headers["Cache-Control"] = "no-store"         # dynamic endpoint: never cache
    return resp


@app.get("/api/whoami")
def whoami():
    # Hit it through the edge and directly to compare: via the edge, peer = edge IP
    # and forwarded_proto = https; directly, the forwarded fields are null.
    resp = jsonify(backend=ID, **client_info())
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/api/catalog")
def catalog():
    # Identical body on A and B => identical ETag => 304 works whichever backend answers
    resp = make_response(jsonify(resource="catalog", version=1,
                                 items=["router", "switch", "firewall"]))
    resp.set_etag(hashlib.sha256(resp.get_data()).hexdigest()[:16])
    resp.headers["Cache-Control"] = "max-age=60"
    return resp.make_conditional(request)              # 304 when If-None-Match matches


@app.get("/health")
def health():
    # uptime resets after a restart, which timestamps the HA failover demo (Ext D)
    resp = jsonify(status="up", backend=ID, port=PORT,
                   uptime_s=int(time.time() - STARTED), requests=_count)
    resp.headers["Cache-Control"] = "no-store"
    return resp


if __name__ == "__main__":
    # 0.0.0.0 => reachable from other Macs on the LAN (NOT 127.0.0.1)
    app.run(host="0.0.0.0", port=PORT)
