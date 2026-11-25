#!/usr/bin/env python3
"""Builds evidence/FINAL_REPORT.md and evidence/index.html from ONE data structure below.
Edit the data (e.g. change a status from 'redo' to 'ok' after a re-run), then:  python3 evidence/build_report.py
"""
import html, os

HERE = os.path.dirname(os.path.abspath(__file__))
M1, M2, M3, M4 = ("../mac1-dns-client/evidence/", "../mac2-edge-lb/evidence/",
                  "../mac3-backend-a/evidence/", "../mac4-backend-b/evidence/")
S = "screenshots/"

TEAM = [("Mac 1", "Mohan", "10.7.9.43", "DNS server (dnsmasq) + main test client", "#7a4dff"),
        ("Mac 2", "Narendra", "10.7.7.27", "Edge: nginx reverse proxy, load balancer, TLS, private CA", "#e8830c"),
        ("Mac 3", "Keshav", "10.7.29.229", "Backend A :3001 + backup DNS + standby edge", "#14a06a"),
        ("Mac 4", "Mayank", "10.7.25.176", "Backend B :3002", "#2f6bff")]

# status: ok | redo | missing
SECTIONS = [
 # ------------------------------------------------------------------ PHASE 1
 dict(id="p1-ip", phase=1, title="1. Network and IP check", status="ok", owner="All four",
  what="Before anything else every Mac proves it is on the same campus Wi-Fi subnet (10.7.0.0/19) and can reach the router.",
  ran=["./scripts/my_ip.sh"],
  saw=["Each Mac prints its IPv4 address, netmask 255.255.224.0, gateway 10.7.0.1 and a router ping with 0% loss.",
       "The campus DHCP server had changed all four IPs, so the team re-ran setup_team.sh and pushed the new team.env (Mohan 10.7.9.43, Narendra 10.7.7.27, Keshav 10.7.29.229, Mayank 10.7.25.176).",
       "Mohan's first run shows a red WARNING: DNS 127.0.2.2 means Cloudflare WARP was ON and would ignore our DNS server. He switched it off (second run, DNS no longer 127.x)."],
  why="DNS, TCP and TLS only work if the IP layer works. Every script also refuses to run if the Mac's IP is not the one in team.env, which stops silent mistakes.",
  shots=[(S+"p1-01-mac1-ip-warp-warning.jpeg", "Mohan: WARNING, a local DNS proxy (WARP) is ON"),
         (S+"p1-05-mac1-warp-off.jpeg", "Mohan: same command after turning WARP off"),
         (S+"p1-02-mac3-ip.jpeg", "Keshav: IP 10.7.29.229, router ping OK"),
         (S+"p1-03-mac4-ip.jpeg", "Mayank: IP 10.7.25.176, router ping OK")]),
 dict(id="p1-dns", phase=1, title="2. Our own DNS server", status="ok", owner="Mohan (Mac 1)",
  what="dnsmasq on Mac 1 answers app.team1.test and api.team1.test with the edge's IP. This is our own mini 'Route 53'.",
  ran=["./scripts/setup_dnsmasq.sh primary"],
  saw=["dnsmasq: syntax check OK, started, listening on UDP 10.7.9.43:53 and 127.0.0.1:53.",
       "Self-test: dig app.team1.test @10.7.9.43 returns A record 10.7.7.27 (the edge)."],
  why="DNS only turns a name into an IP. It never connects to anything. Clients then open TCP and TLS to that IP.",
  shots=[(S+"p1-09-mac1-dnsmasq-primary.jpeg", "dnsmasq running and answering 10.7.7.27")]),
 dict(id="p1-edge", phase=1, title="3. Edge server and private CA", status="ok", owner="Narendra (Mac 2)",
  what="nginx on Mac 2 terminates HTTPS on port 8443 and load-balances to the two backends. A small server hands out the team CA certificate.",
  ran=["./scripts/configure_nginx.sh", "./scripts/serve_ca.sh"],
  saw=["nginx -t successful, nginx listening on *:8443.",
       "serve_ca.sh served http://10.7.7.27:8000/ca.crt; the access lines show all three teammates downloaded it (10.7.9.43, 10.7.25.176, 10.7.29.229)."],
  why="The certificate contains names (SAN) not IPs, so it stays valid even when DHCP changes an IP. Only the public CA is served, private keys never leave Mac 2.",
  shots=[(S+"p1-04-mac2-nginx-up-serve-ca.png", "nginx started and CA server running"),
         (S+"p1-13-mac2-serve-ca-3-downloads.jpeg", "Three downloads of ca.crt from the three teammates")]),
 dict(id="p1-trust", phase=1, title="4. Clients trust the CA and use our DNS", status="ok", owner="Mohan, Keshav, Mayank",
  what="Each client downloads the team CA, installs it as trusted and points its resolver to Mac 1.",
  ran=["./scripts/trust_ca.sh && ./scripts/set_dns.sh primary"],
  saw=["All three print the SAME fingerprint sha256 62:F0:8C:C0:78:C5:16:67:...:2B:31:D9, so everyone trusts the same CA.",
       "networksetup now lists nameserver 10.7.9.43 on every client. Mayank's old manual DNS (1.1.1.1) and Keshav's empty setting were saved first and can be restored with set_dns.sh restore."],
  why="This meets the 'at least two clients resolve through our DNS' requirement (we have three). It is also why curl works without -k.",
  shots=[(S+"p1-10-mac1-trust-ca-set-dns.jpeg", "Mohan"), (S+"p1-12-mac3-trust-ca-set-dns.jpeg", "Keshav"),
         (S+"p1-11-mac4-trust-ca-set-dns.jpeg", "Mayank"), (S+"p1-18-mac3-trust-ca.jpeg", "Keshav, second run (Wi-Fi reconnect)"),
         (S+"p1-19-mac4-trust-ca.jpeg", "Mayank, second run"), (S+"p1-20-mac3-set-dns.jpeg", "Keshav set_dns primary"),
         (S+"p1-22-mac4-set-dns.jpeg", "Mayank set_dns primary")]),
 dict(id="p1-diag", phase=1, title="5. Layer-by-layer check: diagnose.sh", status="ok", owner="Mohan",
  what="One script checks IP, DNS, TCP, TLS, HTTP and the backends in that order. The first FAIL is the real problem.",
  ran=["./scripts/diagnose.sh"],
  saw=["First run: everything PASS except TLS: 'Verify return code: 21 (unable to verify the first certificate)'.",
       "But the HTTP check right below it returned 200 without -k, so the certificate really was trusted. The script was wrong, not the setup.",
       "Cause: the Mac's built-in openssl (LibreSSL) does not read the macOS keychain where trust_ca.sh put the CA. Fix: give openssl the CA file with -CAfile.",
       "After the fix every layer is PASS, including 'certificate verifies'."],
  why="A great viva story: a false alarm found by reading the layers in order, and a fix that took one line.",
  shots=[(S+"p1-14-mac1-diagnose-false-fail.jpeg", "Before: false FAIL at the TLS layer"),
         (S+"p1-15-mac1-diagnose-all-pass.jpeg", "After the fix: all layers PASS")]),
 dict(id="p1-lb", phase=1, title="6. Load balancing", status="ok", owner="Mohan",
  what="Six HTTPS requests to https://app.team1.test:8443/api/status without -k. The X-Backend header tells which backend answered.",
  ran=["./scripts/demo_lb.sh"],
  saw=["The answers alternate between Backend A and Backend B (round-robin), every response is 200 and X-Edge is mac2.",
       "The client never sees a backend IP, only the edge."],
  why="This was the Phase 1 gate. Round-robin is nginx's default strategy.",
  shots=[(S+"p1-16-mac1-demo-lb.jpeg", "First run"), (S+"p1-21-mac1-demo-lb-again.jpeg", "Run from the scripts folder")]),
 dict(id="p1-tls", phase=1, title="7. TLS proof", status="ok", owner="Mohan",
  what="Shows exactly how the secure connection is built and that the certificate is verified.",
  ran=["./scripts/demo_tls.sh"],
  saw=["TLS 1.3 with TLS_AES_256_GCM_SHA384, subject CN=app.team1.test, issuer CN=team1 Local CA, 'SSL certificate verify ok', 'Verify return code: 0 (ok)'.",
       "Forcing TLS 1.2 shows the full handshake (Certificate, Server Key Exchange, Finished), which is what Wireshark can display."],
  why="Chain of trust: client trusts CA, CA signed the edge certificate, name matches the SAN. TLS ends at nginx; edge to backend is plain HTTP inside the LAN.",
  shots=[(S+"p1-17-mac1-demo-tls.jpeg", "demo_tls.sh output")]),
 # ------------------------------------------------------------------ PHASE 2
 dict(id="p2-a", phase=2, title="Ext A: Backup DNS", status="ok", owner="Keshav + Mohan",
  what="A second dnsmasq on Mac 3 gives the same answers. Mohan's Mac lists both DNS servers. We stop the primary and the site must still open.",
  ran=["Keshav: ./scripts/setup_dnsmasq.sh backup", "Mohan: ./scripts/set_dns.sh both", "Mohan: sudo brew services stop dnsmasq  (primary down), then dig and curl"],
  saw=["Both servers answer 10.7.7.27 (EA0).",
       "Primary down: 'connection timed out; no servers could be reached'. Backup still answers 10.7.7.27.",
       "The HTTPS request still returned 200. It took 2.552 s, about the 2 s DNS timeout plus the request."],
  why="The resolver list is tried in order: when the first server does not answer, the Mac asks the next one. Failover works but costs one timeout.",
  shots=[(M3+"EA1-backup-dns.png", "Keshav: backup DNS listening on 10.7.29.229:53 and answering"),
         (M1+"EA2-failover.png", "Mohan: primary dead, backup answers, curl still 200")],
  files=["mac1-dns-client/evidence/EA0-both-answer.txt", "mac1-dns-client/evidence/EA2-failover.txt", "mac3-backend-a/evidence/EA1-backup-dns.txt"]),
 dict(id="p2-b", phase=2, title="Ext B: TTL and caching", status="ok", owner="Mohan (+ Keshav)",
  what="With TTL=30 we change the DNS record to another IP while a script watches two views: dig straight to the server (always fresh) and the Mac's own resolver cache.",
  ran=["TTL=30 ./scripts/setup_dnsmasq.sh primary", "./scripts/demo_ttl.sh  (recording)", "APP_IP=10.7.25.176 TTL=30 ./scripts/setup_dnsmasq.sh primary  (change record)", "flush cache"],
  saw=["11:05:51: dig already shows the new IP 10.7.25.176.",
       "The system resolver kept the OLD IP 10.7.7.27 until 11:06:22, more than 30 s.",
       "At 11:06:27 it switched: this is right after the scheduled cache flush. (We cannot separate natural TTL expiry from the flush here, but the old answer clearly survived the change.)"],
  why="A cached answer can outlive a record change by up to the TTL. For a planned migration you lower the TTL first. TTL is the price of caching.",
  shots=[(M1+"EB-ttl-timeline.png", "Mohan: timeline of dig (fresh) versus system resolver (cached)")],
  files=["mac1-dns-client/evidence/EB-ttl-timeline.txt"], chart="ttl"),
 dict(id="p2-c", phase=2, title="Ext C: Service isolation with pf (firewall)", status="redo", owner="Keshav, Mayank, Narendra, Mohan",
  what="The backends' ports should only accept connections from the edge (Mac 2). Direct access from a client (Mac 1) must time out, but the site through the edge must still work.",
  ran=["Keshav: ./scripts/isolate_pf.sh 3001", "Mayank: ./scripts/isolate_pf.sh 3002", "Narendra and Mohan: test", "Both: ./scripts/rollback_pf.sh"],
  saw=["DONE: the rules are active on both backends: 'pass in quick ... from 10.7.7.27 to any port 3001/3002' followed by 'block drop in quick ... port 3001/3002'.",
       "DONE: rollback_pf.sh printed 'rollback OK (rules identical to before)' on both Macs, so the firewall was restored.",
       "NOT VALID YET, edge test: Narendra's curl failed after 2 ms ('Couldn't connect'). The screenshot shows why: macOS asked 'Allow iTerm to find devices on local networks?' and blocked LAN traffic until allowed.",
       "NOT VALID YET, client test: Mohan's direct curl to both backends returned 200, so pf was not active at the moment he ran it (the stages were run out of order)."],
  why="Least privilege: only the component that needs the port gets it. In the cloud this is a security group. Caveat: source-IP rules can be spoofed on a shared LAN, so this is a concept demo.",
  shots=[(M3+"EC1-pf-on-mac3.png", "Keshav: pf rules on port 3001"), (M4+"EC2-pf-on-mac4.png", "Mayank: pf rules on port 3002"),
         (M3+"EC5-rollback-ok-mac3.png", "Keshav: rollback OK"), (M4+"EC5-rollback-ok-mac4.png", "Mayank: rollback OK"),
         (M2+"EC3-edge-allowed.png", "Narendra: edge test blocked by the macOS Local Network prompt (to redo)"),
         (M1+"EC4-client-blocked.png", "Mohan: direct access still worked, pf was not on yet (to redo)")],
  redo="Allow the terminal in System Settings > Privacy & Security > Local Network. Then everybody: git pull and run ./scripts/phase2.sh 4. Order: Keshav and Mayank turn pf ON first, then Narendra (expect 200), then Mohan (expect timeout and edge still 200). The new script warns Mohan if pf is not active."),
 dict(id="p2-d", phase=2, title="Ext D: High availability (failover)", status="redo", owner="Keshav + Mohan + Narendra",
  what="Stop Backend A: every answer must come from B and users must notice nothing. Start A again and the A/B alternation returns.",
  ran=["Keshav stops Backend A", "Mohan: ./scripts/demo_lb.sh", "Keshav restarts A, wait 15 s", "Mohan: ./scripts/demo_lb.sh", "Narendra: tail the nginx access log"],
  saw=["The stop did not work: Keshav's check still shows 'Python ... TCP *:3001 (LISTEN)'. The script used pkill with 'python', but macOS names the process 'Python', so nothing was killed.",
       "So Mohan's run still alternates A,B,A,B and is not a failover proof.",
       "Useful proof already in the log: the lines 'backend=10.7.25.176:3002, 10.7.29.229:3001 ... rt=2.123' (10:59:56) and 'rt=1.029' (11:04:22) show nginx tried :3002 first, failed within its 2 s connect timeout, and automatically served the request from :3001. That is proxy_next_upstream working."],
  why="Passive health checks: after max_fails=2 errors nginx skips a server for fail_timeout=10 s and retries the request on the next one. The single nginx edge is still the point of failure (Ext E).",
  shots=[(M3+"ED0-A-stopped.png", "Keshav: port 3001 still LISTEN, A was not stopped (to redo)"),
         (M1+"ED1-failover.png", "Mohan: run during the failed stop"), (M1+"ED2-recovery.png", "Mohan: recovery run"),
         (M2+"ED3-access-log.png", "Narendra: access log, note the two-upstream retry lines")],
  files=["mac2-edge-lb/evidence/ED3-access-log.txt"],
  redo="The script is fixed (it now stops the process by port). git pull and run ./scripts/phase2.sh 2 on Keshav, Mohan and Narendra. Expect: during the stop all six answers are B; after the restart A/B again."),
 dict(id="p2-e", phase=2, title="Ext E: Standby edge and DNS cutover", status="ok", owner="Keshav + Mohan + Narendra",
  what="A second nginx on Mac 3 (the standby) uses the same certificate. We then change the DNS record from Mac 2 to Mac 3 and watch the traffic move.",
  ran=["Narendra: ./scripts/serve_certs.sh  (hands the certificate and key to Keshav only)", "Keshav: ./scripts/configure_nginx.sh standby", "Mohan: record change to 10.7.29.229 while ./scripts/demo_edge.sh runs"],
  saw=["Standby answered directly: HTTP/2 200, nginx listening on *:8443 on Mac 3 (EE1).",
       "Timeline: edge=mac2 with ip 10.7.7.27 until 11:08:07; one '?' sample at 11:08:14 (resolver switching); from 11:08:19 edge=standby with ip 10.7.29.229.",
       "The record was changed at about 11:07:51, so the switch took about 28 s, matching the 30 s TTL. Backends kept alternating A/B behind the standby.",
       "phase2_check.sh at the end reports 9 ready, 0 not ready, including 'standby sends X-Edge: standby'."],
  why="This removes the single point of failure by hand: the DNS record decides which edge gets users, and the TTL decides how fast they move. The same certificate works because it holds names, not IPs.",
  shots=[(M3+"EE1-standby.png", "Keshav: standby nginx up on Mac 3"), (M1+"EE2-cutover.png", "Mohan: edge flips from mac2 to standby")],
  files=["mac1-dns-client/evidence/EE2-cutover.txt", "mac3-backend-a/evidence/EE1-standby.txt"], chart="cutover"),
 dict(id="p2-f", phase=2, title="Ext F: Troubleshooting", status="redo", owner="Mohan + Narendra",
  what="Narendra breaks something (stops nginx) and Mohan finds it with diagnose.sh by reading the layers in order.",
  ran=["Mohan: ./scripts/diagnose.sh (healthy)", "Narendra: nginx -s stop", "Mohan: ./scripts/diagnose.sh (fault)", "Narendra restarts nginx", "Mohan: ./scripts/diagnose.sh; ./scripts/phase2_check.sh"],
  saw=["Healthy run: every layer PASS (EF1).",
       "Narendra's log confirms 'nginx is STOPPED (fault injected)' (EF0), but Mohan's 'fault' run is also all PASS, so he ran it before nginx was stopped. It does not show the fault yet.",
       "Final check: all PASS and phase2_check says 9 ready, 0 not ready (EF3)."],
  why="Expected result of the real test: the first FAIL appears at layer 2 (TCP, edge port 8443 not open) and everything above it fails too. That tells you the edge is down, not DNS and not TLS.",
  shots=[(M1+"EF1-diagnose-ok.png", "Healthy"), (M1+"EF2-diagnose-fault.png", "Fault run, still all PASS (to redo)"),
         (M1+"EF3-final-check.png", "Final check: 9 ready, 0 not ready")],
  files=["mac2-edge-lb/evidence/EF0-fault.txt"],
  redo="Narendra runs ./scripts/phase2.sh 6 and stops nginx first and says 'fault injected'; only then Mohan runs his stage 6. The new script warns Mohan if there is no FAIL in the output."),
]

MISSING = [
 "Phase 1 Task F (caching): ./scripts/demo_cache.sh, Cache-Control, ETag and the 304 answer.",
 "Phase 1 Task G (Wireshark): phase1.pcapng with the DNS, TCP handshake, TLS handshake and encrypted data views.",
 "Phase 1 five failure demos: ./scripts/failures.sh 1 to 5, one screenshot each with one sentence of 'why'.",
 "Phase 1 Task A ping matrix (check_lan.sh) and the lsof screenshots that show the backends listening on *:3001 and *:3002.",
 "Phase 2 re-runs: Ext C tests, Ext D real failover, Ext F real fault (see the amber boxes).",
 "Chapter 9 of Docs/CN_Project_Master.pdf: paste the numbers and screenshots from this report.",
]

PROBLEMS = [
 ("Campus DHCP changed every IP", "Scripts refused to run ('does not have IP'). We ran setup_team.sh with the new IPs, pushed team.env and everyone re-cloned. Lesson: IPs are in one file; certificates use names, so they did not need to be rebuilt."),
 ("Cloudflare WARP on Mohan's Mac", "DNS showed 127.0.2.2, so our DNS server was ignored. The script printed a red warning, WARP was turned off."),
 ("diagnose.sh showed a false TLS FAIL", "LibreSSL's openssl does not use the macOS keychain. Fixed by passing the CA file with -CAfile."),
 ("macOS Local Network permission", "iTerm was not allowed to talk to LAN devices, so curl failed after 2 ms. Fix: System Settings > Privacy & Security > Local Network."),
 ("Backend A would not stop", "pkill -f 'python backend.py' is case sensitive; macOS shows 'Python'. Fixed by stopping whatever listens on port 3001."),
 ("Stages run out of order", "Some tests ran before the fault or the firewall was in place. The scripts now print a warning when the expected condition is missing."),
 ("Screenshots", "Auto-screenshots need Screen Recording permission for the terminal app. The text output (.txt) is saved next to every screenshot as a backup."),
]

VIVA = [
 ("Why does DNS not connect to the server?", "DNS only maps a name to an IP using UDP port 53. TCP, TLS and HTTP start afterwards, towards that IP."),
 ("What did the backup DNS test show?", "With the primary stopped the first query timed out, the resolver used the second server, and the page still loaded in 2.55 s."),
 ("What is TTL and what did we measure?", "TTL is how long an answer may be cached. After the record change the Mac kept the old IP for 30+ seconds. The cutover to the standby took about 28 s."),
 ("How does the certificate chain work?", "The client trusts team1 Local CA, the CA signed the edge certificate, and the name app.team1.test is in its SAN. We proved it with 'Verify return code: 0 (ok)'."),
 ("How does nginx survive a dead backend?", "max_fails=2 and fail_timeout=10 s mark it down, proxy_next_upstream retries on the other backend. The log shows a request tried :3002 and was served by :3001 after 2 s."),
 ("What is still a single point of failure?", "The one nginx edge. The standby edge plus a DNS change fixes it manually; keepalived/VRRP or a cloud load balancer would make it automatic."),
 ("What does pf do and how is it like the cloud?", "It filters packets by source and port. Only Mac 2 may reach the backend ports, like a security group. Source IPs can be spoofed on a LAN, so it is a demo of the idea."),
 ("Why was the first TLS check red but curl green?", "curl uses the macOS keychain, the old check used openssl which does not. We pointed openssl at the CA file."),
]

# ---------------------------------------------------------------- helpers
ST = {"ok": ("PASS", "Evidence complete"), "redo": ("RE-RUN", "Evidence incomplete, re-run needed"), "missing": ("TODO", "Not captured yet")}

def md():
    o = []
    o.append("# CN Project: Final Evidence Report (Phase 1 and Phase 2)\n")
    o.append("Team 1 · Private Network Service Platform · 25 Nov 2026 · generated from `evidence/build_report.py`. Open `evidence/index.html` for the illustrated version.\n")
    o.append("## 1. What we built (in one minute)\n")
    o.append("A client opens `https://app.team1.test:8443`. **Our own DNS** (Mac 1) turns the name into the edge's IP. The **nginx edge** (Mac 2) completes the TCP and TLS handshake with a certificate signed by **our own CA**, then **load-balances** the request to **Backend A** (Mac 3) or **Backend B** (Mac 4). Everything runs on four laptops on one Wi-Fi, no cloud. Phase 2 breaks and hardens it: backup DNS, TTL, firewall isolation, failover, a standby edge, and troubleshooting.\n")
    o.append("```\nClient -> DNS (Mac1, UDP 53) -> nginx edge (Mac2, TCP+TLS 8443) -> Backend A (Mac3 :3001) / Backend B (Mac4 :3002)\n```\n")
    o.append("| Mac | Owner | IP | Role |\n|---|---|---|---|")
    for m, n, ip, r, _ in TEAM: o.append(f"| {m} | {n} | `{ip}` | {r} |")
    o.append("\n## 2. Result at a glance\n")
    o.append("| Task | Owner | Status |\n|---|---|---|")
    for s in SECTIONS:
        o.append(f"| {s['title']} | {s['owner']} | **{ST[s['status']][0]}** |")
    o.append("\n**PASS** = evidence captured and valid. **RE-RUN** = part of the evidence was captured at the wrong moment; exact fix below. Honest status matters more than a green table.\n")
    for ph, name in ((1, "Phase 1: Build and observe"), (2, "Phase 2: Harden and recover")):
        o.append(f"\n## {2 + ph}. {name}\n")
        for s in [x for x in SECTIONS if x["phase"] == ph]:
            o.append(f"### {s['title']}  `{ST[s['status']][0]}`\n")
            o.append(f"**Owner:** {s['owner']}\n\n**What we did:** {s['what']}\n\n**Commands:**\n```bash\n" + "\n".join(s['ran']) + "\n```\n")
            o.append("**What the evidence shows:**\n" + "\n".join(f"- {x}" for x in s['saw']) + "\n")
            o.append(f"**Why it works:** {s['why']}\n")
            if s.get("redo"): o.append(f"> **Re-run needed:** {s['redo']}\n")
            for p, c in s["shots"]: o.append(f"![{c}]({p})\n*{c}*\n")
            if s.get("files"): o.append("Raw logs: " + ", ".join(f"`{f}`" for f in s["files"]) + "\n")
    o.append("\n## 5. Problems we hit and how we fixed them\n")
    o.append("| Problem | What happened and the fix |\n|---|---|")
    for a, b in PROBLEMS: o.append(f"| {a} | {b} |")
    o.append("\n## 6. Still to do before submission\n")
    for m in MISSING: o.append(f"- [ ] {m}")
    o.append("\n## 7. Viva: short answers\n")
    for q, a in VIVA: o.append(f"**{q}** {a}\n")
    return "\n".join(o) + "\n"

E = html.escape
CSS = """
:root{--ink:#1c2433;--mute:#5c6a82;--line:#e4e9f2;--soft:#f6f8fc;--blue:#2f6bff;--green:#14a06a;--orange:#e8830c;--purple:#7a4dff;--red:#d93d4a}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--blue);text-decoration:none}.wrap{max-width:1100px;margin:auto;padding:0 20px}
.hero{background:linear-gradient(120deg,#e8f0ff 0%,#f0eaff 45%,#fff2e0 100%);border-bottom:1px solid var(--line);padding:56px 0 40px}
.hero h1{margin:0 0 8px;font-size:clamp(28px,5vw,46px);letter-spacing:-.02em}.hero p{margin:0;color:var(--mute);font-size:18px;max-width:780px}
.pill{display:inline-block;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:700;letter-spacing:.04em}
.ok{background:#e3f7ee;color:var(--green)}.redo{background:#fff2e0;color:#b86400}.miss{background:#fdeaec;color:var(--red)}
nav{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav .in{max-width:1100px;margin:auto;padding:8px 20px;display:flex;gap:4px;overflow-x:auto;white-space:nowrap}nav a{padding:6px 12px;border-radius:99px;color:var(--mute);font-size:14px}nav a:hover{background:#e8f0ff;color:var(--blue)}
section{padding:40px 0;border-top:1px solid var(--line)}h2{font-size:30px;margin:0 0 6px}h3{margin:0 0 4px;font-size:22px}.sub{color:var(--mute);margin:0 0 22px}
.grid{display:grid;gap:16px}.g4{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{border:1px solid var(--line);border-radius:16px;padding:18px;background:#fff;box-shadow:0 1px 2px rgba(20,30,60,.04)}
.sec{border:1px solid var(--line);border-radius:18px;margin:22px 0;overflow:hidden;background:#fff}
.sec>.head{padding:16px 20px;display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;background:var(--soft);border-bottom:1px solid var(--line)}
.sec .body{padding:18px 20px}.owner{color:var(--mute);font-size:14px}
.lbl{font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);margin:14px 0 4px}
pre{background:#0f1729;color:#e6edff;padding:12px 14px;border-radius:12px;overflow:auto;font:13.5px/1.55 ui-monospace,Menlo,monospace;margin:6px 0}
ul{margin:4px 0;padding-left:20px}li{margin:4px 0}
.why{border-left:4px solid var(--blue);background:#e8f0ff;padding:10px 14px;border-radius:0 12px 12px 0;margin-top:12px}
.redo-box{border-left:4px solid var(--orange);background:#fff2e0;padding:10px 14px;border-radius:0 12px 12px 0;margin-top:12px}
.shots{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));margin-top:14px}
figure{margin:0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}
figure img{display:block;width:100%;height:auto;cursor:zoom-in;background:#111}figcaption{padding:8px 12px;font-size:13.5px;color:var(--mute)}
table{width:100%;border-collapse:collapse;font-size:15px}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}th{background:var(--soft);font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:14px}
.team{border-top:5px solid var(--c)}.team b{font-size:18px}.team code,code{background:var(--soft);border:1px solid var(--line);padding:1px 6px;border-radius:6px;font-size:13px}
.flow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0}.flow .n{padding:10px 14px;border-radius:12px;font-weight:700;border:2px solid}.flow .a{color:var(--mute);font-weight:800}
.tl{display:flex;flex-wrap:wrap;gap:4px;margin:10px 0}.tl span{padding:4px 8px;border-radius:8px;font:12px ui-monospace,Menlo,monospace;color:#fff}
.legend{font-size:13px;color:var(--mute)}
details{border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:8px 0}summary{cursor:pointer;font-weight:600}
#lb{position:fixed;inset:0;background:rgba(10,15,30,.88);display:none;align-items:center;justify-content:center;z-index:50;cursor:zoom-out}#lb img{max-width:96vw;max-height:94vh;border-radius:10px;background:#111}
footer{padding:30px 0;color:var(--mute);text-align:center;border-top:1px solid var(--line);font-size:14px}
.big{font-size:34px;font-weight:800}.kpi .l{color:var(--mute);font-size:13px}
"""

def chart_ttl():
    rows = [("11:05:31","10.7.7.27","10.7.7.27"),("11:05:36","10.7.7.27","10.7.7.27"),("11:05:41","10.7.7.27","10.7.7.27"),("11:05:46","10.7.7.27","10.7.7.27"),
            ("11:05:51","10.7.7.27","10.7.25.176"),("11:05:57","10.7.7.27","10.7.25.176"),("11:06:02","10.7.7.27","10.7.25.176"),("11:06:07","10.7.7.27","10.7.25.176"),
            ("11:06:12","10.7.7.27","10.7.25.176"),("11:06:17","10.7.7.27","10.7.25.176"),("11:06:22","10.7.7.27","10.7.25.176"),("11:06:27","10.7.25.176","10.7.25.176"),
            ("11:06:32","10.7.25.176","10.7.25.176")]
    c = lambda ip: "#2f6bff" if ip == "10.7.7.27" else "#e8830c"
    a = "".join(f'<span style="background:{c(r[2])}" title="{r[0]}">{r[0][3:]}</span>' for r in rows)
    b = "".join(f'<span style="background:{c(r[1])}" title="{r[0]}">{r[0][3:]}</span>' for r in rows)
    return ('<div class="lbl">Timeline (every 5 s). Blue = old IP 10.7.7.27, orange = new IP 10.7.25.176</div>'
            f'<div class="legend">dig straight to the DNS server (always fresh)</div><div class="tl">{a}</div>'
            f'<div class="legend">the Mac\'s own resolver cache (system)</div><div class="tl">{b}</div>')

def chart_cut():
    rows = [("11:07:36","mac2"),("11:07:41","mac2"),("11:07:46","mac2"),("11:07:52","mac2"),("11:07:57","mac2"),("11:08:02","mac2"),("11:08:07","mac2"),
            ("11:08:14","?"),("11:08:19","standby"),("11:08:24","standby"),("11:08:29","standby"),("11:08:34","standby"),("11:08:40","standby"),("11:08:45","standby")]
    col = {"mac2": "#e8830c", "standby": "#14a06a", "?": "#d93d4a"}
    a = "".join(f'<span style="background:{col[e]}">{t[3:]} {e}</span>' for t, e in rows)
    return ('<div class="lbl">Which edge answered, every 5 s</div><div class="tl">' + a + '</div>'
            '<div class="legend">Orange = Mac 2 · red ? = request during the switch · green = standby on Mac 3. Record changed at about 11:07:51, first standby answer at 11:08:19 (about 28 s, TTL was 30 s).</div>')

def page():
    ok = sum(s["status"] == "ok" for s in SECTIONS); redo = sum(s["status"] == "redo" for s in SECTIONS)
    shots = sum(len(s["shots"]) for s in SECTIONS)
    o = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CN Project Evidence Report</title><style>{CSS}</style></head><body>']
    o.append('<div class="hero"><div class="wrap"><span class="pill ok">TEAM 1 · 25 NOV 2026</span><h1>CN Project: what we built and the proof</h1>'
             '<p>Our own DNS, our own certificate authority, an HTTPS load balancer and two backends on four laptops. Below: every step, the exact command, the screenshot, and why it works.</p></div></div>')
    o.append('<nav><div class="in"><a href="#top">Overview</a><a href="#glance">At a glance</a><a href="#phase1">Phase 1</a><a href="#phase2">Phase 2</a><a href="#problems">Problems and fixes</a><a href="#todo">To do</a><a href="#viva">Viva</a></div></nav><div id="top"></div>')
    o.append('<section><div class="wrap"><h2>How a request travels</h2><p class="sub">Four laptops, one job each.</p><div class="flow">'
             '<div class="n" style="border-color:#2f6bff;background:#e8f0ff">Client</div><div class="a">→ DNS</div><div class="n" style="border-color:#7a4dff;background:#f0eaff">Mac 1 · dnsmasq</div>'
             '<div class="a">→ TCP + TLS</div><div class="n" style="border-color:#e8830c;background:#fff2e0">Mac 2 · nginx edge</div><div class="a">→</div>'
             '<div class="n" style="border-color:#14a06a;background:#e3f7ee">Mac 3 · Backend A</div><div class="a">or</div><div class="n" style="border-color:#14a06a;background:#e3f7ee">Mac 4 · Backend B</div></div>'
             '<div class="grid g4" style="margin-top:18px">' +
             "".join(f'<div class="card team" style="--c:{c}"><b>{E(m)} · {E(n)}</b><br><code>{ip}</code><br><span class="owner">{E(r)}</span></div>' for m, n, ip, r, c in TEAM) +
             '</div></div></section>')
    o.append(f'<section id="glance"><div class="wrap"><h2>Result at a glance</h2><p class="sub">Honest status: green = valid evidence, amber = captured at the wrong moment, re-run needed.</p>'
             f'<div class="grid g4"><div class="card kpi"><div class="big" style="color:var(--green)">{ok}</div><div class="l">tasks with complete evidence</div></div>'
             f'<div class="card kpi"><div class="big" style="color:var(--orange)">{redo}</div><div class="l">tasks to re-run (10 minutes)</div></div>'
             f'<div class="card kpi"><div class="big" style="color:var(--blue)">{shots}</div><div class="l">screenshots in this report</div></div>'
             f'<div class="card kpi"><div class="big" style="color:var(--purple)">4</div><div class="l">Macs, 4 owners</div></div></div>'
             '<div class="scroll" style="margin-top:18px"><table><tr><th>Task</th><th>Owner</th><th>Status</th></tr>' +
             "".join(f'<tr><td><a href="#{s["id"]}">{E(s["title"])}</a></td><td>{E(s["owner"])}</td><td><span class="pill {s["status"] if s["status"]!="missing" else "miss"}">{ST[s["status"]][0]}</span></td></tr>' for s in SECTIONS) +
             '</table></div></div></section>')
    for ph, name, sub in ((1, "Phase 1: Build and observe", "Make it work, then watch it work."), (2, "Phase 2: Harden and recover", "Break it on purpose and show it recovers.")):
        o.append(f'<section id="phase{ph}"><div class="wrap"><h2>{name}</h2><p class="sub">{sub}</p>')
        for s in [x for x in SECTIONS if x["phase"] == ph]:
            cls = s["status"] if s["status"] != "missing" else "miss"
            o.append(f'<div class="sec" id="{s["id"]}"><div class="head"><div><h3>{E(s["title"])}</h3><div class="owner">{E(s["owner"])}</div></div><span class="pill {cls}">{ST[s["status"]][1].upper()}</span></div><div class="body">')
            o.append(f'<div class="lbl">What we did</div><div>{E(s["what"])}</div>')
            o.append('<div class="lbl">Commands</div><pre>' + E("\n".join(s["ran"])) + '</pre>')
            o.append('<div class="lbl">What the evidence shows</div><ul>' + "".join(f'<li>{E(x)}</li>' for x in s["saw"]) + '</ul>')
            if s.get("chart") == "ttl": o.append(chart_ttl())
            if s.get("chart") == "cutover": o.append(chart_cut())
            o.append(f'<div class="why"><b>Why it works:</b> {E(s["why"])}</div>')
            if s.get("redo"): o.append(f'<div class="redo-box"><b>Re-run needed:</b> {E(s["redo"])}</div>')
            o.append('<div class="shots">' + "".join(f'<figure><img loading="lazy" src="{p}" alt="{E(c)}"><figcaption>{E(c)}</figcaption></figure>' for p, c in s["shots"]) + '</div>')
            if s.get("files"): o.append('<div class="lbl">Raw logs</div><div>' + " ".join(f'<code>{E(f)}</code>' for f in s["files"]) + '</div>')
            o.append('</div></div>')
        o.append('</div></section>')
    o.append('<section id="problems"><div class="wrap"><h2>Problems we hit and how we fixed them</h2><p class="sub">Real issues from the lab, each one a good viva answer.</p><div class="scroll"><table><tr><th>Problem</th><th>What happened and the fix</th></tr>' +
             "".join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td></tr>' for a, b in PROBLEMS) + '</table></div></div></section>')
    o.append('<section id="todo"><div class="wrap"><h2>Still to do before submission</h2><p class="sub">Tick these off.</p><div class="card">' +
             "".join(f'<label style="display:flex;gap:10px;padding:8px 0;border-bottom:1px dashed var(--line)"><input type="checkbox" style="width:18px;height:18px;margin-top:5px"><span>{E(m)}</span></label>' for m in MISSING) + '</div></div></section>')
    o.append('<section id="viva"><div class="wrap"><h2>Viva: short answers</h2><p class="sub">Click a question.</p>' +
             "".join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in VIVA) + '</div></section>')
    o.append('<footer>CN Project · team1 · Mohan · Narendra · Keshav · Mayank · generated by evidence/build_report.py</footer>')
    o.append('<div id="lb"><img alt=""></div><script>const lb=document.getElementById("lb"),im=lb.querySelector("img");document.addEventListener("click",e=>{if(e.target.matches("figure img")){im.src=e.target.src;lb.style.display="flex"}else if(lb.style.display==="flex"){lb.style.display="none"}});document.addEventListener("keydown",e=>{if(e.key==="Escape")lb.style.display="none"});</script></body></html>')
    return "\n".join(o)

if __name__ == "__main__":
    open(os.path.join(HERE, "FINAL_REPORT.md"), "w").write(md())
    open(os.path.join(HERE, "index.html"), "w").write(page())
    missing = [p for s in SECTIONS for p, _ in s["shots"] if not os.path.exists(os.path.normpath(os.path.join(HERE, p)))]
    print("written FINAL_REPORT.md and index.html; missing images:", missing or "none")
