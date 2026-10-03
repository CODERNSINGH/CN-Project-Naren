#!/usr/bin/env python3
"""Minimal REST backend for the CN project. The network is the project, not the app."""
import os, time, hashlib
from flask import Flask, jsonify, request, make_response

ID = os.environ.get("BACKEND_ID", "A")                 # "A" or "B"
PORT = int(os.environ.get("BACKEND_PORT", "3001"))     # 3001 (A) / 3002 (B)

app = Flask(__name__)


@app.after_request
def add_backend_header(resp):
    resp.headers["X-Backend"] = ID                     # proves which backend answered
    return resp


@app.get("/")
def index():
    return jsonify(message="Backend %s is running" % ID, port=PORT)


@app.get("/api/status")
def status():
    resp = jsonify(backend=ID, status="ok", time=int(time.time()))
    resp.headers["Cache-Control"] = "no-store"         # dynamic endpoint: never cache
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
    return jsonify(status="up", backend=ID)


if __name__ == "__main__":
    # 0.0.0.0 => reachable from other Macs on the LAN (NOT 127.0.0.1)
    app.run(host="0.0.0.0", port=PORT)
