#!/usr/bin/env python3
"""Generates CN_Project_Architecture.excalidraw (open at https://excalidraw.com -> Open / drag & drop).
Run:  python3 _shared/diagram/build_excalidraw.py
"""
import json, random, textwrap, os, sys, re

random.seed(7)
EL = []
_n = [0]

C = {  # fill, stroke
    "blue":   ("#a5d8ff", "#1971c2"),
    "green":  ("#b2f2bb", "#2f9e44"),
    "orange": ("#ffd8a8", "#e8590c"),
    "purple": ("#d0bfff", "#6741d9"),
    "red":    ("#ffc9c9", "#e03131"),
    "yellow": ("#ffec99", "#f08c00"),
    "gray":   ("#e9ecef", "#495057"),
    "cyan":   ("#99e9f2", "#0c8599"),
    "white":  ("#ffffff", "#1e1e1e"),
}
FONT_SANS, FONT_MONO, FONT_HAND = 2, 3, 1


def _id():
    _n[0] += 1
    return "el%04d" % _n[0]


def base(t, x, y, w, h, **kw):
    e = {
        "id": _id(), "type": t, "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": kw.get("stroke", "#1e1e1e"), "backgroundColor": kw.get("fill", "transparent"),
        "fillStyle": "solid", "strokeWidth": kw.get("sw", 2), "strokeStyle": kw.get("style", "solid"),
        "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": kw.get("round", None), "seed": random.randint(1, 2**31 - 1),
        "version": 1, "versionNonce": random.randint(1, 2**31 - 1), "isDeleted": False,
        "boundElements": None, "updated": 1767000000000, "link": None, "locked": False,
    }
    return e


def rect(x, y, w, h, color="white", style="solid", sw=2, rounded=True):
    f, s = C[color]
    e = base("rectangle", x, y, w, h, fill=f, stroke=s, style=style, sw=sw,
             round={"type": 3} if rounded else None)
    EL.append(e)
    return e


def est_w(s, size, mono=False):
    k = 0.62 if mono else 0.55
    return max(len(l) for l in s.split("\n")) * size * k


def text(x, y, s, size=14, w=None, align="left", color="#1e1e1e", font=FONT_SANS):
    lines = s.split("\n")
    lh = size * 1.25
    ww = w if w else est_w(s, size, font == FONT_MONO) + 6
    e = base("text", x, y, ww, lh * len(lines), stroke=color)
    e.update({
        "text": s, "originalText": s, "fontSize": size, "fontFamily": font,
        "textAlign": align, "verticalAlign": "top", "baseline": int(size), "containerId": None,
        "lineHeight": 1.25, "autoResize": False,
    })
    EL.append(e)
    return e


def wrap(lines, w, size, mono=False):
    k = 0.62 if mono else 0.55
    cpl = max(10, int((w - 28) / (size * k)))
    out = []
    for l in lines:
        if not l:
            out.append("")
            continue
        indent = len(l) - len(l.lstrip())
        sub = textwrap.wrap(l, cpl, subsequent_indent=" " * (indent + 2)) or [l]
        out.extend(sub)
    return out


def box(x, y, w, title, lines, color="white", size=14, tsize=18, mono=False, h=None, style="solid"):
    body = wrap(lines, w, size, mono)
    hh = 14 + tsize * 1.25 + 8 + len(body) * size * 1.25 + 14
    if h:
        hh = max(hh, h)
    rect(x, y, w, hh, color, style)
    text(x + 12, y + 12, title, tsize, w - 24, "left", C[color][1])
    if body:
        text(x + 12, y + 12 + tsize * 1.25 + 8, "\n".join(body), size, w - 24, "left", "#1e1e1e",
             FONT_MONO if mono else FONT_SANS)
    return hh


def banner(y, title, sub=None, w=2700, color="gray"):
    rect(0, y, w, 64 if not sub else 84, color)
    text(20, y + 10, title, 30, w - 40, "left", C[color][1], FONT_HAND)
    if sub:
        text(20, y + 50, sub, 15, w - 40, "left", "#343a40")
    return y + (64 if not sub else 84) + 30


def arrow(x1, y1, x2, y2, color="#1e1e1e", style="solid", sw=2, head=True, start_head=False, label=None,
          lsize=13, lcolor=None, loff=-20, lw=None):
    e = base("arrow", x1, y1, abs(x2 - x1), abs(y2 - y1), stroke=color, style=style, sw=sw)
    e.update({"points": [[0, 0], [x2 - x1, y2 - y1]], "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None,
              "startArrowhead": "arrow" if start_head else None,
              "endArrowhead": "arrow" if head else None, "elbowed": False})
    EL.append(e)
    if label:
        mx = (x1 + x2) / 2
        w = lw or max(abs(x2 - x1), est_w(label, lsize) + 10)
        text(mx - w / 2, (y1 + y2) / 2 + loff, label, lsize, w, "center", lcolor or color)
    return e


def line(x1, y1, x2, y2, color="#868e96", style="dashed", sw=1):
    return arrow(x1, y1, x2, y2, color, style, sw, head=False)


def polyline(points, color="#1e1e1e", style="solid", sw=2, head=True):
    x0, y0 = points[0]
    e = base("arrow", x0, y0, max(p[0] for p in points) - min(p[0] for p in points),
             max(p[1] for p in points) - min(p[1] for p in points), stroke=color, style=style, sw=sw)
    e.update({"points": [[p[0] - x0, p[1] - y0] for p in points], "lastCommittedPoint": None,
              "startBinding": None, "endBinding": None, "startArrowhead": None,
              "endArrowhead": "arrow" if head else None, "elbowed": False})
    EL.append(e)


def table(x, y, widths, rows, header_color="blue", row_h=None, size=13, mono_cols=()):
    """rows[0] is header. Auto row height by wrapped text. Returns bottom y."""
    cy = y
    for ri, row in enumerate(rows):
        wrapped = [wrap(c.split("\n"), widths[i], size, i in mono_cols) for i, c in enumerate(row)]
        rh = max(len(w_) for w_ in wrapped) * size * 1.25 + 18
        rh = max(rh, row_h or 0)
        cx = x
        for ci, cell in enumerate(row):
            col = header_color if ri == 0 else ("white" if ri % 2 else "gray")
            rect(cx, cy, widths[ci], rh, col, rounded=False, sw=1)
            text(cx + 10, cy + 9, "\n".join(wrapped[ci]), size + (1 if ri == 0 else 0), widths[ci] - 16,
                 "left", C[header_color][1] if ri == 0 else "#1e1e1e",
                 FONT_MONO if (ci in mono_cols and ri > 0) else FONT_SANS)
            cx += widths[ci]
        cy += rh
    return cy


# ======================================================================== TITLE
y = 0
rect(0, y, 2700, 150, "yellow")
text(30, y + 14, "CN Project — Private Network Service Platform  (team1)", 44, 2600, "left", "#e8590c", FONT_HAND)
text(30, y + 76, "Client → private DNS (Mac 1) → HTTPS edge / load balancer (Mac 2) → Backend A (Mac 3) / Backend B (Mac 4)   |   "
     "Phase 1: Build & Observe   ·   Phase 2: Harden & Recover   ·   Final: Explain & Defend", 18, 2600)
text(30, y + 108, "\"The application stays simple — the network is the project.\"   Repo: github.com/CODERNSINGH/CN-Project-Naren   ·   "
     "Sections: 1 Topology · 2 Request flow · 3 Layers · 4 Phase 1 tasks · 5 Failures · 6 Phase 2 · 7 Build order · 8 Demo + troubleshooting · 9 Repo + ports", 15, 2600, "left", "#495057")
y += 190

# ======================================================================== 1 TOPOLOGY
y = banner(y, "1. Network topology — four roles on ONE private LAN (one subnet, no router hop between Macs)",
           "Roles are a network topology, not a software architecture.  IPs live in team.env (MAC1_IP … MAC4_IP) — get yours with ./scripts/my_ip.sh")
rect(0, y, 2000, 56, "cyan")
text(20, y + 8, "Same private Wi-Fi / hotspot / LAN   (e.g. 192.168.1.0/24, gateway = router)", 20, 1960, "center", C["cyan"][1])
text(20, y + 34, "Rules: all Macs same network · VPN off · iCloud Private Relay off · router AP/client isolation OFF · hosts reach each other via ARP → MAC, gateway only for outside destinations", 13, 1960, "center", "#343a40")
by = y + 150
mac = [
    ("blue", "Mac 1 — DNS server + TEST CLIENT", "mac1-dns-client/",
     ["IP: MAC1_IP", "dnsmasq on :53 (UDP+TCP)", "zone team1.test (local, not forwarded)", "app.team1.test → MAC2_IP", "api.team1.test → MAC2_IP", "client tools: dig, curl, browser, Wireshark", "demos + diagnose.sh + failures.sh", "Cloud ≈ Amazon Route 53"]),
    ("green", "Mac 2 — EDGE: nginx proxy + LB + TLS (THIS laptop)", "mac2-edge-lb/",
     ["IP: MAC2_IP   (the only IP clients ever learn)", "nginx :8443 HTTPS (8080 → redirect)", "terminates TLS, cert = app.team1.test (SAN)", "upstream round-robin → MAC3:3001, MAC4:3002", "passive health: max_fails=2 fail_timeout=10s", "adds header X-Edge: mac2", "owns the team CA (make_certs.sh, serve_ca.sh)", "Cloud ≈ AWS ALB / CDN edge"]),
    ("orange", "Mac 3 — BACKEND A  (+ Phase 2 extras)", "mac3-backend-a/",
     ["IP: MAC3_IP", "Flask REST on 0.0.0.0:3001", "header X-Backend: A", "/  /api/status  /api/catalog  /health", "Phase 2: backup dnsmasq (Ext A)", "Phase 2: standby nginx, X-Edge: standby (Ext E)", "Phase 2: pf firewall → only Mac 2 → :3001 (Ext C)", "Cloud ≈ EC2 / container instance A"]),
    ("orange", "Mac 4 — BACKEND B", "mac4-backend-b/",
     ["IP: MAC4_IP", "Flask REST on 0.0.0.0:3002", "header X-Backend: B", "same endpoints, same /api/catalog ETag as A", "Phase 2: pf firewall → only Mac 2 → :3002 (Ext C)", "keeps the evidence folder / report", "Cloud ≈ EC2 / container instance B"]),
]
mx = 0
for col, t, folder, ls in mac:
    h = box(mx, by, 485, t, ls, col, size=14, tsize=16)
    text(mx + 12, by + h + 6, "folder: " + folder, 14, 460, "left", C[col][1], FONT_MONO)
    arrow(mx + 242, by, mx + 242, y + 56, C[col][1], sw=3, head=False)
    mx += 505
# legend
box(2060, y, 640, "Legend / colours used in all diagrams",
    ["blue = DNS (Mac 1)", "green = edge / TLS / load balancer (Mac 2)", "orange = backends (Mac 3, 4)", "purple = TLS handshake / security", "red = failure / blocked", "yellow = Phase 2 items", "cyan = LAN", "dashed = optional / standby / next request"], "white", 14, 17)
y = by + 330

# ======================================================================== 2 REQUEST FLOW
y = banner(y, "2. One request, end to end — what happens when the client opens https://app.team1.test:8443/api/status",
           "Every step can be proven with a tool: dig (DNS) · tcp.flags.syn (TCP) · tls.handshake (TLS) · curl -v / DevTools (HTTP) · X-Backend / X-Edge headers (LB)")
cols = [("Client (Mac 1)", "purple", 170), ("DNS server (Mac 1 · dnsmasq)", "blue", 570), ("Edge (Mac 2 · nginx)", "green", 970),
        ("Backend A (Mac 3 :3001)", "orange", 1370), ("Backend B (Mac 4 :3002)", "orange", 1770)]
hy = y
for t, col, cx in cols:
    rect(cx - 150, hy, 300, 70, col)
    text(cx - 140, hy + 14, t, 17, 280, "center", C[col][1])
Y0 = hy + 70
for t, col, cx in cols:
    line(cx, Y0, cx, Y0 + 740, C[col][1])
CL, DN, ED, BA, BB = 170, 570, 970, 1370, 1770
BL, TC, TL, HT, GR = "#1971c2", "#495057", "#6741d9", "#2f9e44", "#e8590c"
arrow(CL, Y0 + 50, DN, Y0 + 50, BL, label="(1) DNS query  A? app.team1.test   (UDP, ephemeral port → 53)")
arrow(DN, Y0 + 105, CL, Y0 + 105, BL, label="(2) answer: A = MAC2_IP, TTL   (DNS only finds the IP)")
arrow(CL, Y0 + 180, ED, Y0 + 180, TC, label="(3) TCP SYN   (ephemeral port → MAC2_IP:8443)")
arrow(ED, Y0 + 220, CL, Y0 + 220, TC, label="SYN-ACK")
arrow(CL, Y0 + 260, ED, Y0 + 260, TC, label="ACK   → connection established (4-tuple)")
arrow(CL, Y0 + 320, ED, Y0 + 320, TL, label="(4) TLS ClientHello  (SNI = app.team1.test, versions, key share)")
arrow(ED, Y0 + 365, CL, Y0 + 365, TL, label="ServerHello + Certificate (signed by team CA) + Finished")
arrow(CL, Y0 + 410, ED, Y0 + 410, TL, label="Client verifies chain+SAN → Finished → keys derived")
arrow(CL, Y0 + 480, ED, Y0 + 480, HT, sw=3, label="(5) HTTP GET /api/status   (encrypted inside TLS records)")
arrow(ED, Y0 + 540, BA, Y0 + 540, GR, label="(6) plain HTTP :3001  (round-robin: turn 1)")
arrow(ED, Y0 + 580, BB, Y0 + 580, GR, style="dashed", label="(6) plain HTTP :3002  (turn 2 = next request)")
arrow(BA, Y0 + 630, ED, Y0 + 630, GR, label="200 JSON + X-Backend: A")
arrow(ED, Y0 + 690, CL, Y0 + 690, HT, sw=3, label="(7) 200 JSON + X-Backend + X-Edge: mac2   (encrypted)")
nx = 1980
notes = [
    (Y0 + 20, "blue", "DNS — Task B", ["Stub resolver → dnsmasq; UDP/53 (TCP only for big answers).", "dig bypasses the OS cache, curl/browser use mDNSResponder."]),
    (Y0 + 150, "gray", "TCP — Task G", ["SYN → SYN-ACK → ACK; ACK = ISN+1; sequence numbers give reliability, window = flow control."]),
    (Y0 + 285, "purple", "TLS — Task E", ["Cert must chain to a trusted CA and SAN must match the name. TLS 1.3 encrypts the Certificate; force --tlsv1.2 to show it in Wireshark."]),
    (Y0 + 450, "green", "HTTP + load balancing — Tasks D, F", ["nginx terminates TLS, then HTTP/1.1 to the backend. Client never learns backend IPs. /api/catalog has Cache-Control+ETag → 304."]),
    (Y0 + 590, "orange", "Return path", ["Backend adds X-Backend, nginx adds X-Edge, TLS re-encrypts to the client."]),
]
for ny, col, t, ls in notes:
    box(nx, ny, 700, t, ls, col, 13, 15)
y = Y0 + 790

# ======================================================================== 3 LAYERS
y = banner(y, "3. OSI vs TCP/IP — where every protocol in this project sits, and how a packet is wrapped",
           "Moving data through the core: app data → TLS → TCP segment → IP packet → Ethernet/Wi-Fi frame → next hop MAC (via ARP, same subnet = no router)")
rows = [
    ["OSI layer", "TCP/IP layer", "Protocols / artefacts in this project", "Evidence / Wireshark filter"],
    ["7 Application", "Application", "DNS, HTTP/1.1 (HTTP/2 optional), REST/JSON, Cache-Control, ETag", "dns · http (after key log) · curl -v"],
    ["6 Presentation", "Application", "TLS encryption + X.509 certificate encoding", "tls.handshake · tls.record.content_type==23"],
    ["5 Session", "Application", "TLS session setup / resumption (placement 5/6 is debated — say so in viva)", "tls.handshake.type==1 / 2 / 11"],
    ["4 Transport", "Transport", "TCP :8443, :3001, :3002 · UDP :53 (DNS) · ports = sockets", "tcp.flags.syn==1 · Statistics → Conversations"],
    ["3 Network", "Internet", "IPv4 addresses (MAC1_IP…MAC4_IP), ICMP (ping), default gateway", "ip.addr==MAC2_IP · ping"],
    ["2 Data link", "Link", "Ethernet / Wi-Fi frames, MAC addresses, ARP", "arp · arp -a · ifconfig en0 (ether)"],
    ["1 Physical", "Link", "Wi-Fi radio / cable", "—"],
]
yb = table(0, y, [190, 170, 760, 560], rows, "blue", size=14)
# encapsulation nested boxes
ex = 1780
text(ex, y - 2, "Encapsulation of ONE HTTPS request", 17, 700, "left", "#1971c2")
nest = [("gray", "Ethernet / Wi-Fi frame  (dst MAC = Mac 2, via ARP)"), ("cyan", "IP packet  (src MAC1_IP → dst MAC2_IP)"),
        ("yellow", "TCP segment  (src port ephemeral → dst 8443, seq/ack, window)"), ("purple", "TLS record  (encrypted, type 23 application data)"),
        ("green", "HTTP request  GET /api/status  Host: app.team1.test")]
nx0, ny0, nw, nh = ex, y + 30, 900, 330
for i, (col, label) in enumerate(nest):
    pad = i * 34
    rect(nx0 + pad, ny0 + pad, nw - 2 * pad, nh - 2 * pad, col)
    text(nx0 + pad + 12, ny0 + pad + 6, label, 14, nw - 2 * pad - 24, "left", C[col][1])
y = max(yb, ny0 + nh) + 40
box(0, y, 1300, "Transport-layer notes for the viva",
    ["Socket pair (4-tuple) = (client IP, client ephemeral port, edge IP, 8443) uniquely identifies the connection.",
     "Reliability: sequence numbers number bytes, ACKs confirm, loss → retransmission (timeout / dup ACKs), checksum detects corruption.",
     "Flow control = receiver window (protects receiver). Congestion control = cwnd, slow start, AIMD (protects network).",
     "TCP = connection-oriented, reliable. UDP = connectionless (DNS, QUIC/HTTP3). DNS uses UDP/53 for small answers, TCP for big ones."], "white", 14, 17)
box(1380, y, 1320, "Explanation-only topics (brief says no build needed)",
    ["HTTP/1.1: one request at a time per connection · HTTP/2: multiplexed streams, binary framing, HPACK, but TCP head-of-line blocking · HTTP/3: QUIC over UDP/443, TLS 1.3 built in.",
     "Email: SMTP 25/587/465 sends/relays · IMAP 143/993 keeps mail on server · POP3 110/995 downloads · routing uses DNS MX records.",
     "CDN: replicate cacheable content at edge nodes, DNS/anycast steers users, Cache-Control/ETag decide freshness — our nginx is one edge node."], "gray", 14, 17)
y += 240

# ======================================================================== 4 PHASE 1 TASKS
y = banner(y, "4. Phase 1 — Build & Observe: seven mandatory tasks (gate: client resolves app.team1.test, connects over HTTPS, gets answers from BOTH backends)",
           "Marks: Review 1 = 50 (40 team + 10 viva).  Task A+B 10 · C+D 10 · E 8 · G 7 · F 5 · viva 10")
tasks = [
    ("cyan", "Task A — Private LAN   [Mac: all]", ["Join same Wi-Fi; record IP, mask, gateway, interface, MAC.", "Ping every pair (12 directed pairs).", "Draw topology diagram.", "RUN: ./scripts/my_ip.sh · ./scripts/check_lan.sh", "EVIDENCE: IP table, ping screenshots, diagram"]),
    ("blue", "Task B — Private DNS   [Mac 1]", ["brew install dnsmasq; records app/api → MAC2_IP.", "≥2 clients use Mac 1 as resolver.", "Access app by NAME only.", "RUN: ./scripts/setup_dnsmasq.sh primary · ./scripts/set_dns.sh primary", "VERIFY: dig app.team1.test · nslookup · scutil --dns", "EVIDENCE: dnsmasq.conf, dig from 2 clients"]),
    ("orange", "Task C — Two backends   [Mac 3, Mac 4]", ["Flask REST, bind 0.0.0.0 (not 127.0.0.1).", "GET /  ·  GET /api/status → {backend, status}", "Header X-Backend: A|B on every response.", "Ports A=3001, B=3002.", "RUN: ./backend/run_backend.sh", "EVIDENCE: curl -i from ANOTHER Mac, lsof showing *:3001"]),
    ("green", "Task D — Edge proxy + LB   [Mac 2]", ["nginx upstream with both backends, round-robin (or least_conn).", "Repeated curl alternates A,B,A,B.", "Why clients never need backend IPs.", "RUN: ./scripts/configure_nginx.sh", "VERIFY: ./scripts/demo_lb.sh", "EVIDENCE: nginx.conf, nginx -t, loop output"]),
    ("purple", "Task E — HTTPS / TLS   [Mac 2 + trust on clients]", ["Local CA + server cert with SAN (OpenSSL).", "nginx terminates TLS on 8443.", "CA installed on every client → no warnings, NO curl -k.", "RUN: ./scripts/make_certs.sh · serve_ca.sh · (clients) trust_ca.sh", "VERIFY: ./scripts/demo_tls.sh → Verify return code 0 (ok)", "EXPLAIN: ClientHello→ServerHello→Certificate→Key exchange→Finished"]),
    ("yellow", "Task F — HTTP caching   [any client]", ["/api/catalog: Cache-Control: max-age=60 + ETag.", "/api/status: no-store (dynamic).", "Show curl -I, then If-None-Match → 304.", "Browser DevTools shows memory/disk cache.", "RUN: ./scripts/demo_cache.sh", "EXPLAIN: fresh hit vs conditional (304) vs full 200"]),
    ("red", "Task G — Protocol flow capture   [Mac 1 Wireshark]", ["Flush DNS, make a fresh request, capture on en0.", "Show: DNS q/a (53/UDP) · TCP SYN/SYN-ACK/ACK · TLS ClientHello/ServerHello/Cert · encrypted data · alternating X-Backend.", "Save evidence/phase1.pcapng (+ tls12.pcapng with --tlsv1.2).", "RUN: ./scripts/capture.sh phase1 (CLI) or Wireshark GUI"]),
    ("gray", "Phase 1 gate checklist", ["[ ] ping matrix all OK", "[ ] dig → MAC2_IP from 2 Macs", "[ ] both backends reachable from another Mac", "[ ] https://app.team1.test:8443 works, no warning, no -k", "[ ] X-Backend alternates A/B", "[ ] Cache-Control + 304 shown", "[ ] pcapng saved", "[ ] 5 failure demos documented"]),
]
gx, gy, hmax = 0, y, 0
for i, (col, t, ls) in enumerate(tasks):
    if i == 4:
        gx, gy, hmax = 0, gy + hmax + 24, 0
    w = 655
    h = box(gx, gy, w, t, ls, col, 14, 16)
    hmax = max(hmax, h)
    gx += w + 27
    if i == 3:
        pass
y = gy + hmax + 50

# ======================================================================== 5 FAILURES
y = banner(y, "5. Phase 1 — five deliberate failures: break it, observe, explain which layer failed",
           "Run on the client Mac 1:  ./scripts/failures.sh 1 … 5     (isolating the layer is the skill being graded)")
fails = [
    ("red", "(1) Wrong DNS server on client", ["BREAK: client DNS → unused IP", "SEE: dig times out; ping MAC2_IP still works; curl --resolve works", "WHY: DNS and IP are independent layers; DNS only maps names→IPs", "LAYER: application (DNS)"]),
    ("red", "(2) DNS record → wrong IP", ["BREAK: APP_IP=MAC4_IP ./setup_dnsmasq.sh primary + flush", "SEE: dig succeeds, but client lands on the wrong host (refused / cert mismatch)", "WHY: DNS is a directory, not a connection — it can't know if the target is right or alive", "LAYER: DNS data"]),
    ("red", "(3) One backend stopped", ["BREAK: Ctrl+C Backend A", "SEE: all answers X-Backend: B, status 200", "WHY: nginx marks A failed (max_fails/fail_timeout) and proxy_next_upstream retries on B; first request may wait ≤2 s connect timeout", "LAYER: upstream"]),
    ("red", "(4) Both backends stopped", ["BREAK: stop A and B", "SEE: DNS ok, TLS ok (verify 0), but HTTP 502 Bad Gateway", "WHY: edge healthy, upstream dead — shows where the edge ends and the backend begins", "LAYER: upstream / app"]),
    ("red", "(5) Wrong destination port", ["BREAK: curl https://app.team1.test:9999", "SEE: ping ok, TCP refused (SYN → RST,ACK) or timeout", "WHY: ports and IPs are separate identifiers; nothing listens on 9999", "LAYER: transport"]),
]
gx, hmax = 0, 0
for col, t, ls in fails:
    h = box(gx, y, 520, t, ls, col, 14, 16)
    hmax = max(hmax, h)
    gx += 545
y += hmax + 40
rows = [["Failure", "Layer", "Symptom", "What still works"],
        ["Wrong DNS server", "DNS", "lookup fails / timeout", "ping by IP"],
        ["Wrong DNS record", "DNS data", "wrong destination reached", "DNS answers normally"],
        ["One backend down", "upstream", "none for clients (failover)", "HTTPS, DNS, backend B"],
        ["Both backends down", "upstream", "502 Bad Gateway", "DNS, TCP, TLS to the edge"],
        ["Wrong port", "transport", "connection refused / timeout", "DNS, ICMP ping"]]
y = table(0, y, [380, 260, 560, 460], rows, "red", size=14) + 40

# ======================================================================== 6 PHASE 2
y = banner(y, "6. Phase 2 — Harden, Recover, Troubleshoot (extends Phase 1, no rebuild)",
           "Gate: backup DNS, TTL behaviour, service isolation, HA failover and ≥1 troubleshooting challenge demonstrated.  Marks: A,B,D 15 · C,E 10 · F 10 · report 5 · viva 10")
# resilient architecture diagram
ay = y
box(0, ay, 380, "Client (Mac 1)", ["resolvers: Mac 1 THEN backup", "set_dns.sh both"], "purple", 13, 16)
box(480, ay - 6, 380, "Primary DNS (Mac 1)", ["Ext A: sudo brew services stop dnsmasq", "→ timeout on 1st resolver"], "red", 13, 16, style="dashed")
box(480, ay + 130, 380, "Backup DNS (Mac 3)", ["setup_dnsmasq.sh backup", "same records → answers instead"], "blue", 13, 16)
box(980, ay - 6, 400, "Edge nginx (Mac 2)  X-Edge: mac2", ["SPOF in current design!", "Ext D: passive health checks"], "green", 13, 16)
box(980, ay + 130, 400, "STANDBY nginx (Mac 3)  X-Edge: standby", ["same config + same cert (valid for the NAME)", "Ext E: DNS cutover target"], "yellow", 13, 16, style="dashed")
box(1500, ay - 6, 360, "Backend A (Mac 3 :3001)", ["pf: only Mac 2 may connect (Ext C)", "stopped → traffic to B only"], "orange", 13, 16)
box(1500, ay + 130, 360, "Backend B (Mac 4 :3002)", ["pf: only Mac 2 (+standby) may connect"], "orange", 13, 16)
arrow(380, ay + 30, 480, ay + 30, "#e03131", style="dashed", label="1st", loff=-18)
arrow(380, ay + 60, 480, ay + 170, "#1971c2", label="fallback", loff=-6)
arrow(860, ay + 40, 980, ay + 40, "#2f9e44", label="", loff=-18)
arrow(860, ay + 175, 980, ay + 175, "#f08c00", style="dashed", label="DNS → standby", loff=-18)
arrow(1380, ay + 40, 1500, ay + 40, "#e8590c")
arrow(1380, ay + 60, 1500, ay + 170, "#e8590c", style="dashed")
text(1900, ay, "Reading the picture:", 16, 780, "left", "#495057")
text(1900, ay + 26, "• solid = normal path, dashed = failover / optional path\n• Ext A removes DNS as a single point of failure\n• Ext D keeps service alive when one backend dies\n• Ext E removes the edge SPOF by DNS cutover\n• Ext C hides backends from every client except the edge\n• remaining SPOFs: the LAN/router, the CA, DNS cache time (TTL)", 14, 780)
y = ay + 290
ext = [
    ("blue", "Ext A — Backup DNS resolver", ["Second dnsmasq on Mac 3 with identical records; clients list both resolvers (set_dns.sh both).", "Stop dnsmasq on Mac 1 → names still resolve via backup (short delay: resolver tries servers in order after a timeout).", "EXPLAIN: DNS failure (resolution stops) vs application failure (resolution works, service down)."]),
    ("yellow", "Ext B — DNS TTL & controlled change", ["TTL=30 ./scripts/setup_dnsmasq.sh primary (host-record with TTL).", "Resolve from client, change record to another IP, run ./scripts/demo_ttl.sh → old answer persists ≤ TTL, then new.", "Flush: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder → immediate change.", "EXPLAIN: lower TTL before migrations (Route 53 blue/green)."]),
    ("red", "Ext C — Service isolation (pf)", ["./scripts/isolate_pf.sh 3001|3002 on Mac 3/4 — allow only Mac 2, block rest (drop = silent timeout).", "Prove: Mac 2 → backend OK; Mac 1 → backend times out; via the edge by name still works.", "./scripts/rollback_pf.sh restores original rules (rollback copy kept).", "EXPLAIN: least privilege, cloud security groups; source-IP rules can be spoofed."]),
    ("green", "Ext D — HA failover", ["nginx: max_fails=2 fail_timeout=10s, proxy_connect_timeout 2s, proxy_next_upstream error timeout 5xx.", "Stop Backend A → every response X-Backend: B; restart → A/B resume after fail_timeout.", "Open-source nginx = PASSIVE checks only (active health_check is nginx Plus).", "SPOF: edge nginx → fix with 2 edges + VRRP/keepalived, health-checked DNS, or cloud LB."]),
    ("orange", "Ext E — Edge migration (DNS cutover)", ["Standby nginx on Mac 3 (configure_nginx.sh standby) with same config + cert; header X-Edge: standby.", "Lower TTL to 30 s, then TTL=30 APP_IP=MAC3_IP ./setup_dnsmasq.sh primary; watch ./scripts/demo_edge.sh.", "OBSERVE: cached clients still hit mac2 until TTL expires; new lookups reach standby.", "Optional: nginx -s stop on Mac 2 → service still up."]),
    ("purple", "Ext F — Faculty-injected fault", ["Faculty breaks one thing; diagnose OUT LOUD in layer order, partial credit for method.", "./scripts/diagnose.sh runs: LAN/IP → DNS → TCP → TLS → HTTP/app → backends and prints the suspect for the first FAIL.", "Check logs: tail -f $(brew --prefix)/var/log/nginx/error.log · tail /tmp/dnsmasq.log"]),
]
gx, gy, hmax = 0, y, 0
for i, (col, t, ls) in enumerate(ext):
    if i == 3:
        gx, gy, hmax = 0, gy + hmax + 24, 0
    h = box(gx, gy, 880, t, ls, col, 14, 17)
    hmax = max(hmax, h)
    gx += 910
y = gy + hmax + 50

# ======================================================================== 7 BUILD ORDER
y = banner(y, "7. Build order — who runs what, in which order (full detail in each Mac's README and GUIDE_END_TO_END.md)",
           "Step 0 everywhere:  git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren  ·  cd <your folder>  ·  ./scripts/my_ip.sh → send IP to lead → lead runs ./setup_team.sh IP1 IP2 IP3 IP4 team1, pushes → everyone git pull")
rows = [["#", "Mac", "Command", "Success looks like"],
        ["1", "all", "./scripts/my_ip.sh  then  ./scripts/check_lan.sh", "IP known; every ping in the matrix is OK"],
        ["2", "lead (Mac 2)", "./setup_team.sh MAC1_IP MAC2_IP MAC3_IP MAC4_IP team1 ; git add -A ; git commit ; git push", "team.env + all 4 folders updated; others git pull"],
        ["3", "Mac 3", "./backend/run_backend.sh   (leave running)", "Running on http://0.0.0.0:3001"],
        ["4", "Mac 4", "./backend/run_backend.sh   (leave running)", "Running on http://0.0.0.0:3002"],
        ["5", "Mac 1", "curl -i http://MAC3_IP:3001/api/status ; curl -i http://MAC4_IP:3002/api/status", "JSON + X-Backend A / B from ANOTHER Mac"],
        ["6", "Mac 1", "./scripts/setup_dnsmasq.sh primary", "dig +short app.team1.test @MAC1_IP prints MAC2_IP"],
        ["7", "Mac 2", "brew install nginx ; ./scripts/make_certs.sh", "openssl verify → app.crt: OK"],
        ["8", "Mac 2", "./scripts/configure_nginx.sh", "nginx -t ok; LISTEN on 8443"],
        ["9", "Mac 2", "./scripts/serve_ca.sh   (leave running briefly)", "http://MAC2_IP:8000/ca.crt downloadable"],
        ["10", "Mac 1, 3, 4", "./scripts/trust_ca.sh  then  ./scripts/set_dns.sh primary", "https://app.team1.test:8443 works, no warning"],
        ["11", "Mac 1", "./scripts/demo_lb.sh   → PHASE 1 GATE", "X-Backend alternates A,B,A,B"],
        ["12", "Mac 1", "demo_cache.sh · demo_tls.sh · Wireshark / capture.sh · failures.sh 1..5", "Tasks E, F, G + 5 failure demos recorded"],
        ["13", "Mac 3", "setup_dnsmasq.sh backup ; configure_nginx.sh standby (after copying certs)", "Ext A + Ext E ready"],
        ["14", "Mac 3, 4", "./scripts/isolate_pf.sh PORT … ./scripts/rollback_pf.sh", "Ext C: client blocked, edge allowed, rollback OK"],
        ["15", "Mac 1", "./scripts/diagnose.sh · demo_ttl.sh · demo_edge.sh", "Ext B, E, F"]]
y = table(0, y, [60, 190, 1360, 1050], rows, "green", size=14, mono_cols=(2,)) + 40

# ======================================================================== 8 DEMO + TROUBLESHOOTING
y = banner(y, "8. Final demonstration (11 steps, in this order) and the troubleshooting ladder",
           "Faculty may stop at any step to ask questions.  Every member must speak and answer individual viva questions from understanding, not notes.")
demo = [
    ("1", "Topology + IP/service inventory", "diagram, IP table, service map"), ("2", "All Macs on the private LAN", "ping matrix, show each IP"),
    ("3", "Resolve the private domain", "dig app.team1.test → MAC2_IP via Mac 1"), ("4", "HTTPS by NAME", "padlock, no warning, no IP, no -k"),
    ("5", "Load balancing", "demo_lb.sh → A,B,A,B"), ("6", "Wireshark evidence", "DNS, TCP handshake, TLS handshake, encrypted data"),
    ("7", "HTTP headers + caching", "curl -I Cache-Control, 304 / cache hit"), ("8", "Fail one backend", "stop Mac 3 → still served by B"),
    ("9", "Phase 2 resilience", "backup DNS / TTL / DNS cutover (A/B/E)"), ("10", "Diagnose injected fault", "layer by layer, out loud"),
    ("11", "Individual viva", "everyone explains any part"),
]
dy = y
for i, (n, t, d) in enumerate(demo):
    cx = (i % 2) * 640
    cy = dy + (i // 2) * 92
    rect(cx, cy, 620, 78, "cyan" if i < 8 else "yellow")
    text(cx + 12, cy + 8, n + ".  " + t, 17, 596, "left", "#0c8599")
    text(cx + 12, cy + 40, d, 14, 596)
dend = dy + 6 * 92
# ladder
lx = 1330
text(lx, dy - 4, "Troubleshooting ladder — stop at the FIRST failing step (./scripts/diagnose.sh does this)", 17, 1350, "left", "#e03131")
ladder = [
    ("0 LAN / IP", "ping gateway ; ping MAC2_IP", "Wi-Fi, VPN, wrong network, ICMP blocked", "cyan"),
    ("1 DNS", "dig app.team1.test ; scutil --dns ; dscacheutil -q host -a name …", "wrong client resolver, dnsmasq down, wrong record, stale cache", "blue"),
    ("2 TCP", "nc -vz MAC2_IP 8443 ; lsof -nP -iTCP:8443", "nginx down, wrong port, firewall, wrong bind address", "gray"),
    ("3 TLS", "openssl s_client -connect app.team1.test:8443 -servername app.team1.test", "expired cert, SAN mismatch, CA not trusted, wrong key/cert pair", "purple"),
    ("4 HTTP / app", "curl -vi https://app.team1.test:8443/api/status", "502/504 upstream down or wrong upstream, 404 nginx config", "green"),
    ("5 Backends", "curl -i http://MAC3_IP:3001/health", "app stopped, bound to 127.0.0.1, pf rule blocking", "orange"),
    ("6 Logs", "tail -f nginx error.log · tail /tmp/dnsmasq.log", "shows the failing component", "yellow"),
]
ly = dy + 28
for i, (st, cmd, sus, col) in enumerate(ladder):
    x = lx + i * 28
    rect(x, ly + i * 82, 1330 - i * 28, 72, col)
    text(x + 10, ly + i * 82 + 6, st + "   —  " + cmd, 14, 1310 - i * 28, "left", C[col][1], FONT_MONO)
    text(x + 10, ly + i * 82 + 40, "suspect: " + sus, 14, 1310 - i * 28)
    if i < len(ladder) - 1:
        arrow(x + 14, ly + i * 82 + 72, x + 14 + 28, ly + (i + 1) * 82, "#e03131", sw=2)
y = max(dend, ly + len(ladder) * 82) + 40

# ======================================================================== 9 REPO + PORTS
y = banner(y, "9. Repository layout, ports and deliverables")
box(0, y, 900, "Repo layout (GitHub: CODERNSINGH/CN-Project-Naren)",
    ["team.env           ← the 4 IPs + team name (edit via ./setup_team.sh)", "sync.sh            ← copies team.env + _shared into the 4 folders, builds dist/*.zip",
     "setup_team.sh      ← one command to set all IPs", "_shared/common    ← scripts + nginx template used by every Mac",
     "_shared/mac2      ← make_certs.sh, serve_ca.sh", "_shared/backend   ← backend.py (Flask), run_backend.sh",
     "mac1-dns-client/  mac2-edge-lb/  mac3-backend-a/  mac4-backend-b/", "   each: README.md (steps) · scripts/ · team.env · evidence/ (· backend/)",
     "README.md  GUIDE_END_TO_END.md  DEMO_RUNBOOK.md  EVIDENCE_CHECKLIST.md  VIDEO_SCRIPT.md",
     "Docs/ (brief + master PDFs)   CN_Project_Architecture.excalidraw (this file)"], "gray", 13, 17, mono=True)
rows = [["Port / proto", "Who", "Purpose"],
        ["53 UDP (+TCP)", "dnsmasq Mac 1 (+Mac 3 backup)", "private DNS, zone team1.test"],
        ["8443 TCP", "nginx Mac 2 (+standby Mac 3)", "HTTPS: TLS termination + LB"],
        ["8080 TCP", "nginx Mac 2", "HTTP → HTTPS redirect (optional)"],
        ["3001 TCP", "Backend A Mac 3", "REST app (X-Backend: A)"],
        ["3002 TCP", "Backend B Mac 4", "REST app (X-Backend: B)"],
        ["8000 TCP", "Mac 2 serve_ca.sh", "temporary: share PUBLIC ca.crt only"],
        ["49152–65535", "client", "ephemeral source ports"]]
table(940, y, [220, 420, 500], rows, "blue", size=14)
rows = [["Deliverable", "Where it comes from"],
        ["Architecture document", "this diagram + IP table + Docs/CN_Project_Master.pdf"],
        ["Configuration bundle", "generated/dnsmasq.conf, generated/nginx.conf, scripts/, cert notes, pf rules"],
        ["Backend source code", "_shared/backend/ (GitHub repo link)"],
        ["Evidence folder", "evidence/ — see EVIDENCE_CHECKLIST.md"],
        ["Phase 2 report", "Docs/CN_Project_Master.pdf chapter 9 (fill TODOs)"],
        ["Final presentation + video", "DEMO_RUNBOOK.md · VIDEO_SCRIPT.md"]]
yy = y + 330
table(940, yy, [330, 810], rows, "yellow", size=14)
y += 700

text(0, y, "Single points of failure → fixes:  edge nginx (2 edges + VRRP/keepalived, health-checked DNS, cloud LB) · DNS (backup resolver) · LAN/router (redundant paths) · one CA/cert (rotate, 2 issuers)", 16, 2600, "left", "#e03131")
text(0, y + 30, "Cloud map:  dnsmasq = Route 53 · nginx = ALB / CDN edge · backends = EC2 / containers · pf = security groups · DNS cutover = Route 53 weighted / failover routing · mkcert/OpenSSL CA = ACM / private CA", 16, 2600, "left", "#1971c2")

# ---- substitute real IPs / owners from team.env
REAL_IPS = {}
_envp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "team.env")
for _l in open(_envp):
    _m = re.match(r"^([A-Z0-9_]+)=([^ #]+)", _l.strip())
    if _m: REAL_IPS[_m.group(1)] = _m.group(2)
_titles = {"Mac 1 — DNS server + TEST CLIENT": "MAC1_OWNER", "Mac 2 — EDGE: nginx proxy + LB + TLS (THIS laptop)": "MAC2_OWNER",
           "Mac 3 — BACKEND A  (+ Phase 2 extras)": "MAC3_OWNER", "Mac 4 — BACKEND B": "MAC4_OWNER"}
for _e in EL:
    if _e["type"] != "text": continue
    t = _e["text"]
    for _k in ("BACKUP_DNS_IP", "STANDBY_EDGE_IP", "MAC1_IP", "MAC2_IP", "MAC3_IP", "MAC4_IP"):
        if _k in REAL_IPS and REAL_IPS[_k] != "PENDING": t = t.replace(_k, REAL_IPS[_k])
    for _tt, _ok in _titles.items():
        if t == _tt and _ok in REAL_IPS: t = t + "  — " + REAL_IPS[_ok]
    _e["text"] = _e["originalText"] = t

doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": EL,
       "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"}, "files": {}}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "CN_Project_Architecture.excalidraw")
out = os.path.normpath(out)
json.dump(doc, open(out, "w"), indent=1)
print("wrote", out, len(EL), "elements, canvas height ~", int(y + 80))
