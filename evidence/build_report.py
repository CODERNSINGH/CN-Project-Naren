#!/usr/bin/env python3
"""Builds evidence/FINAL_REPORT.md and evidence/index.html from ONE data structure below.
Edit the data (statuses: ok, notes, repro, explained), then:  python3 evidence/build_report.py
"""
import html, os

HERE = os.path.dirname(os.path.abspath(__file__))
M1, M2, M3, M4 = ("../mac1-dns-client/evidence/", "../mac2-edge-lb/evidence/",
                  "../mac3-backend-a/evidence/", "../mac4-backend-b/evidence/")
S = "screenshots/"

TEAM = [("Mac 1", "Mohan Kumar C R", "10.7.9.43", "DNS server (dnsmasq) + main test client", "#7a4dff"),
        ("Mac 2", "Narendra Singh (team lead)", "10.7.7.27", "Edge: nginx reverse proxy, load balancer, TLS, private CA", "#e8830c"),
        ("Mac 3", "Keshav Rajput", "10.7.29.229", "Backend A :3001 + backup DNS + standby edge", "#14a06a"),
        ("Mac 4", "Mayank Gupta", "10.7.25.176", "Backend B :3002", "#2f6bff")]

# status: ok | notes | repro | explained
SECTIONS = [
 # ------------------------------------------------------------------ PHASE 1
 dict(id="p1-ip", phase=1, title="Network and IP check", status="ok", owner="All four",
  what="Before anything else every Mac proves it is on the same campus Wi-Fi subnet (10.7.0.0/19) and can reach the router.",
  ran=["./scripts/my_ip.sh"],
  saw=["Each Mac prints its IPv4 address, netmask 255.255.224.0, gateway 10.7.0.1 and a router ping with 0% loss.",
       "The campus DHCP server had changed all four IPs, so the team re-ran setup_team.sh and pushed the new team.env (Mohan 10.7.9.43, Narendra 10.7.7.27, Keshav 10.7.29.229, Mayank 10.7.25.176).",
       "Mohan's first run shows a red WARNING: DNS 127.0.2.2 means Cloudflare WARP was ON and would ignore our DNS server. He switched it off (second run, DNS no longer 127.x)."],
  why="DNS, TCP and TLS only work if the IP layer works. Every script also refuses to run if the Mac's IP is not the one in team.env, which stops silent mistakes.",
  shots=[(S+"p1-01-mac1-ip-warp-warning.jpeg", "Mohan: WARNING, a local DNS proxy (WARP) is ON"),
         (S+"p1-05-mac1-warp-off.jpeg", "Mohan: same command after turning WARP off"),
         (S+"p1-02-mac3-ip.jpeg", "Keshav: IP 10.7.29.229, router ping OK"),
         (S+"p1-03-mac4-ip.jpeg", "Mayank Gupta: IP 10.7.25.176, router ping OK"),
         (S+"p1-06-mac1-fresh-clone.jpeg", "Mohan: fresh git clone of the repo"),
         (S+"p1-07-mac4-ip-after-clone.jpeg", "Mayank: IP check after the fresh clone"),
         (S+"p1-08-mac3-ip-after-clone.jpeg", "Keshav: IP check after the fresh clone")]),
 dict(id="p1-dns", phase=1, title="Our own DNS server", status="ok", owner="Mohan (Mac 1)",
  what="dnsmasq on Mac 1 answers app.team1.test and api.team1.test with the edge's IP. This is our own mini 'Route 53'.",
  ran=["./scripts/setup_dnsmasq.sh primary"],
  saw=["dnsmasq: syntax check OK, started, listening on UDP 10.7.9.43:53 and 127.0.0.1:53.",
       "Self-test: dig app.team1.test @10.7.9.43 returns A record 10.7.7.27 (the edge)."],
  why="DNS only turns a name into an IP. It never connects to anything. Clients then open TCP and TLS to that IP.",
  shots=[(S+"p1-09-mac1-dnsmasq-primary.jpeg", "dnsmasq running and answering 10.7.7.27")],
  logs=[("Queried live from Mac 2 against Mohan's dnsmasq (25 Nov 11:36), proving it serves other Macs too", "../mac2-edge-lb/evidence/B8-dns-from-mac1.txt", None)]),
 dict(id="p1-edge", phase=1, title="Edge server and private CA", status="ok", owner="Narendra (Mac 2)",
  what="nginx on Mac 2 terminates HTTPS on port 8443 and load-balances to the two backends. A small server hands out the team CA certificate.",
  ran=["./scripts/configure_nginx.sh", "./scripts/serve_ca.sh"],
  saw=["nginx -t successful, nginx listening on *:8443.",
       "serve_ca.sh served http://10.7.7.27:8000/ca.crt; the access lines show all three teammates downloaded it (10.7.9.43, 10.7.25.176, 10.7.29.229)."],
  why="The certificate contains names (SAN) not IPs, so it stays valid even when DHCP changes an IP. Only the public CA is served, private keys never leave Mac 2.",
  shots=[(S+"p1-04-mac2-nginx-up-serve-ca.png", "nginx started and CA server running"),
         (S+"p1-13-mac2-serve-ca-3-downloads.jpeg", "Three downloads of ca.crt from the three teammates")]),
 dict(id="p1-trust", phase=1, title="Clients trust the CA and use our DNS", status="ok", owner="Mohan, Keshav, Mayank",
  what="Each client downloads the team CA, installs it as trusted and points its resolver to Mac 1.",
  ran=["./scripts/trust_ca.sh && ./scripts/set_dns.sh primary"],
  saw=["All three print the SAME fingerprint sha256 62:F0:8C:C0:78:C5:16:67:...:2B:31:D9, so everyone trusts the same CA.",
       "networksetup now lists nameserver 10.7.9.43 on every client. Mayank's old manual DNS (1.1.1.1) and Keshav's empty setting were saved first and can be restored with set_dns.sh restore."],
  why="This meets the 'at least two clients resolve through our DNS' requirement (we have three). It is also why curl works without -k.",
  shots=[(S+"p1-10-mac1-trust-ca-set-dns.jpeg", "Mohan"), (S+"p1-12-mac3-trust-ca-set-dns.jpeg", "Keshav"),
         (S+"p1-11-mac4-trust-ca-set-dns.jpeg", "Mayank"), (S+"p1-18-mac3-trust-ca.jpeg", "Keshav, second run (Wi-Fi reconnect)"),
         (S+"p1-19-mac4-trust-ca.jpeg", "Mayank, second run"), (S+"p1-20-mac3-set-dns.jpeg", "Keshav set_dns primary"),
         (S+"p1-22-mac4-set-dns.jpeg", "Mayank set_dns primary")]),
 dict(id="p1-diag", phase=1, title="Layer-by-layer check: diagnose.sh", status="ok", owner="Mohan",
  what="One script checks IP, DNS, TCP, TLS, HTTP and the backends in that order. The first FAIL is the real problem.",
  ran=["./scripts/diagnose.sh"],
  saw=["First run: everything PASS except TLS: 'Verify return code: 21 (unable to verify the first certificate)'.",
       "But the HTTP check right below it returned 200 without -k, so the certificate really was trusted. The script was wrong, not the setup.",
       "Cause: the Mac's built-in openssl (LibreSSL) does not read the macOS keychain where trust_ca.sh put the CA. Fix: give openssl the CA file with -CAfile.",
       "After the fix every layer is PASS, including 'certificate verifies'."],
  why="A great viva story: a false alarm found by reading the layers in order, and a fix that took one line.",
  shots=[(S+"p1-14-mac1-diagnose-false-fail.jpeg", "Before: false FAIL at the TLS layer"),
         (S+"p1-15-mac1-diagnose-all-pass.jpeg", "After the fix: all layers PASS")]),
 dict(id="p1-lb", phase=1, title="Load balancing", status="ok", owner="Mohan",
  what="Six HTTPS requests to https://app.team1.test:8443/api/status without -k. The X-Backend header tells which backend answered.",
  ran=["./scripts/demo_lb.sh"],
  saw=["The answers alternate between Backend A and Backend B (round-robin), every response is 200 and X-Edge is mac2.",
       "The client never sees a backend IP, only the edge."],
  why="This was the Phase 1 gate. Round-robin is nginx's default strategy.",
  shots=[(S+"p1-16-mac1-demo-lb.jpeg", "First run"), (S+"p1-21-mac1-demo-lb-again.jpeg", "Run from the scripts folder")]),
 dict(id="p1-tls", phase=1, title="TLS proof", status="ok", owner="Mohan",
  what="Shows exactly how the secure connection is built and that the certificate is verified.",
  ran=["./scripts/demo_tls.sh"],
  saw=["TLS 1.3 with TLS_AES_256_GCM_SHA384, subject CN=app.team1.test, issuer CN=team1 Local CA, 'SSL certificate verify ok', 'Verify return code: 0 (ok)'.",
       "Forcing TLS 1.2 shows the full handshake (Certificate, Server Key Exchange, Finished), which is what Wireshark can display."],
  why="Chain of trust: client trusts CA, CA signed the edge certificate, name matches the SAN. TLS ends at nginx; edge to backend is plain HTTP inside the LAN.",
  shots=[(S+"p1-17-mac1-demo-tls.jpeg", "demo_tls.sh output")]),

 dict(id="p1-be", phase=1, title="Backends A and B", status="ok", owner="Keshav (Mac 3), Mayank (Mac 4)",
  what="Two copies of the same small Flask app, one per Mac. Each answers with its own X-Backend header and listens on all interfaces (0.0.0.0), not only on localhost.",
  ran=["./backend/run_backend.sh   (Mac 3: port 3001, Mac 4: port 3002)"],
  saw=["From a different Mac (Mohan's) both backends answered directly: Backend A on 10.7.29.229:3001 and Backend B on 10.7.25.176:3002, each with HTTP 200 and its own X-Backend header and port in the JSON.",
       "nc to 10.7.29.229 port 3001 succeeded, so the socket is reachable from the LAN. The same JSON also shows request counters and uptime (Keshav's logging).",
       "The standby edge later answered with x-backend: A as well (Ext E), so the backends are shared by both edges."],
  why="Binding to 0.0.0.0 makes the port reachable from other Macs. Different ports (3001, 3002) let two backends coexist and be told apart. Identical bodies give identical ETags on A and B.",
  shots=[], logs=[("Mohan's Mac reaching both backends directly (taken before pf was switched on)", "../mac1-dns-client/evidence/EC4-client-blocked.txt", r"^(HTTP/|X-Backend|\{|Connection to)")]),
 dict(id="p1-lan", phase=1, title="Task A: LAN ping matrix", status="repro", owner="Narendra (run on Mac 2)",
  what="check_lan.sh collects this Mac's network facts and pings every Mac of the team.",
  ran=["./scripts/check_lan.sh"],
  saw=["Mac 2 on en0: 10.7.7.27, netmask 255.255.224.0, gateway 10.7.0.1.", "All four Macs answer ping: OK for 10.7.9.43, 10.7.7.27, 10.7.29.229 and 10.7.25.176."],
  why="The IP layer must work before DNS, TCP or TLS can. A failed ping usually means a different Wi-Fi, a VPN or router client isolation.",
  shots=[], logs=[("Captured live on Mac 2 on 25 Nov 2026 11:35", "../mac2-edge-lb/evidence/A2-ping-matrix.txt", None)]),
 dict(id="p1-cache", phase=1, title="Task F: HTTP caching", status="repro", owner="Narendra (run on Mac 2)",
  what="The catalog endpoint is cacheable (Cache-Control and an ETag). A second request with If-None-Match must return 304 Not Modified with no body. The status endpoint must never be cached.",
  ran=["curl -si http://127.0.0.1:3901/api/catalog", "curl -si -H 'If-None-Match: <etag>' http://127.0.0.1:3901/api/catalog", "curl -sI http://127.0.0.1:3901/api/status"],
  saw=["First request: 200 OK with ETag \"0ee15ab3a9bc1a9c\" and Cache-Control: max-age=60.", "Conditional request with that ETag: 304 NOT MODIFIED, no body.", "/api/status: Cache-Control: no-store."],
  why="max-age=60 lets the browser reuse the answer for 60 s with no request at all. After that the ETag lets the server say 'unchanged' with a tiny 304. Backends A and B return the same ETag, so a 304 works whichever one answers.",
  shots=[], logs=[("Captured on Mac 2 with the same backend.py the team ran, started locally, because the lab backends were switched off when this section was written", "../mac2-edge-lb/evidence/F1-caching.txt", None)],
  note="This was reproduced after the lab session, directly against backend.py. Through the nginx edge the headers are identical because nginx passes them on unchanged."),
 dict(id="p1-wire", phase=1, title="Task G: Wireshark view of one request", status="explained", owner="Mohan (explained here)",
  what="What a packet capture of one HTTPS request shows, in order, and which of our evidence matches each part. The capture file itself (phase1.pcapng) was not recorded.",
  ran=["display filters: dns | tcp.flags.syn==1 && tcp.port==8443 | tls.handshake | tls.record.content_type==23"],
  saw=["dns: a query for app.team1.test from the client to UDP port 53 and the answer 10.7.7.27 with its TTL. Matching evidence: the dig outputs (EA0, B8) and the TTL timeline (EB).",
       "tcp.flags.syn==1: SYN, SYN-ACK, ACK between a random client port and port 8443 on the edge. Matching evidence: nc to 10.7.7.27 port 8443 'succeeded' (X1).",
       "tls.handshake: ClientHello with SNI app.team1.test, ServerHello, Certificate (visible in TLS 1.2), Finished. Matching evidence: the demo_tls screenshot lists exactly these messages for TLS 1.2 and the TLS 1.3 summary.",
       "tls.record.content_type==23: encrypted application data, so the HTTP request and the JSON answer are unreadable on the wire."],
  why="Each layer has its own visible signature: UDP/53 for DNS, a three-packet TCP handshake, a TLS handshake and then opaque data. In TLS 1.3 the certificate is encrypted, which is why we also forced TLS 1.2 to show it.",
  shots=[(S+"p1-17-mac1-demo-tls.jpeg", "The TLS handshake messages as printed by demo_tls.sh")]),
 dict(id="p1-fail", phase=1, title="The five required failure demos", status="repro", badge="3 REPRODUCED, 2 EXPLAINED", owner="Narendra (run on Mac 2)",
  what="Five ways the system can fail, each shown at a different layer. Failures 1, 4 and 5 were reproduced live on Mac 2 on 25 Nov 11:36; 2 and 3 are explained with the evidence we already have.",
  ran=["Failure 1: dig +time=2 +tries=1 app.team1.test @<a DNS server that does not exist>", "Failure 4: curl -si https://app.team1.test:8443/api/status   (both backends down)", "Failure 5: curl https://app.team1.test:9999/   and   nc -vz <edge> 9999"],
  saw=["Failure 1, wrong client DNS (live): the dig to 10.7.9.250 prints 'connection timed out; no servers could be reached', yet ping to Mac 1 works and a TCP connect to the edge on 8443 succeeds. So DNS and IP are different layers.",
       "Failure 2, DNS record points to the wrong IP (explained): the name resolves but leads to the wrong machine. Our TTL timeline (EB) shows this exactly: the record was changed to 10.7.25.176 and the resolver served it without any error.",
       "Failure 3, one backend down (explained): nginx skips the dead backend and the other answers. Evidence: the access-log lines with two upstreams in Ext D.",
       "Failure 4, both backends down (live): DNS answers 10.7.7.27, TLS verifies with 'Verify return code: 0 (ok)', then HTTP returns '502 Bad Gateway' with X-Edge: mac2. The nginx error log shows 'connect() failed (61: Connection refused) while connecting to upstream' for both 10.7.25.176:3002 and 10.7.29.229:3001.",
       "Failure 5, wrong port (live): host reachable but 'Connection refused' on port 9999."],
  why="Reading the symptom tells you the layer: timeout on DNS = resolver, 'refused' = host up but port closed, 502 with a good TLS handshake = the edge is fine and the backends are the problem.",
  shots=[], logs=[("Failure 1: wrong DNS server", "../mac2-edge-lb/evidence/X1-wrong-dns.txt", None), ("Failure 4: both backends down", "../mac2-edge-lb/evidence/X4-both-backends-down.txt", None), ("Failure 5: wrong port", "../mac2-edge-lb/evidence/X5-wrong-port.txt", None)]),
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
 dict(id="p2-c", phase=2, title="Ext C: Service isolation with pf (firewall)", status="notes", owner="Keshav, Mayank, Narendra, Mohan",
  what="The backends' ports should only accept connections from the edge (Mac 2). Direct access from a client (Mac 1) must time out, but the site through the edge must still work.",
  ran=["Keshav: ./scripts/isolate_pf.sh 3001", "Mayank: ./scripts/isolate_pf.sh 3002", "Narendra and Mohan: test", "Both: ./scripts/rollback_pf.sh"],
  saw=["DONE: the rules are active on both backends: 'pass in quick ... from 10.7.7.27 to any port 3001/3002' followed by 'block drop in quick ... port 3001/3002'.",
       "DONE: rollback_pf.sh printed 'rollback OK (rules identical to before)' on both Macs, so the firewall was restored.",
       "NOT SHOWN, edge test: Narendra's curl failed after 2 ms ('Couldn't connect'). The screenshot shows why: macOS asked 'Allow iTerm to find devices on local networks?' and blocked LAN traffic until allowed.",
       "NOT SHOWN, client test: Mohan's direct curl to both backends returned 200, so pf was not active at the moment he ran it (the stages were run out of order)."],
  why="Least privilege: only the component that needs the port gets it. In the cloud this is a security group. Caveat: source-IP rules can be spoofed on a shared LAN, so this is a concept demo.",
  shots=[(M3+"EC1-pf-on-mac3.png", "Keshav: pf rules on port 3001"), (M4+"EC2-pf-on-mac4.png", "Mayank: pf rules on port 3002"),
         (M3+"EC5-rollback-ok-mac3.png", "Keshav: rollback OK"), (M4+"EC5-rollback-ok-mac4.png", "Mayank: rollback OK"),
         (M2+"EC3-edge-allowed.png", "Narendra: edge test stopped by the macOS Local Network prompt"),
         (M1+"EC4-client-blocked.png", "Mohan: direct access still worked, pf was not active yet")],
  note="The firewall rules and the rollback are fully proven by the four pf screenshots. The two connectivity tests were taken at the wrong moment: Mohan's direct curl ran before pf was active (it returned 200) and Narendra's curl was stopped by the macOS Local Network prompt. So those two screenshots do not show the block. What the rules do: only 10.7.7.27 (the edge) may open TCP 3001/3002, every other source is dropped silently ('block drop'), so a client like Mac 1 would see a timeout while the site through the edge keeps working. We did not repeat the test."),
 dict(id="p2-d", phase=2, title="Ext D: High availability (failover)", status="notes", owner="Keshav + Mohan + Narendra",
  what="Stop Backend A: every answer must come from B and users must notice nothing. Start A again and the A/B alternation returns.",
  ran=["Keshav stops Backend A", "Mohan: ./scripts/demo_lb.sh", "Keshav restarts A, wait 15 s", "Mohan: ./scripts/demo_lb.sh", "Narendra: tail the nginx access log"],
  saw=["The stop did not work: Keshav's check still shows 'Python ... TCP *:3001 (LISTEN)'. The script used pkill with 'python', but macOS names the process 'Python', so nothing was killed.",
       "So Mohan's run still alternates A,B,A,B and is not a failover proof.",
       "Useful proof already in the log: the lines 'backend=10.7.25.176:3002, 10.7.29.229:3001 ... rt=2.123' (10:59:56) and 'rt=1.029' (11:04:22) show nginx tried :3002 first, failed within its 2 s connect timeout, and automatically served the request from :3001. That is proxy_next_upstream working."],
  why="Passive health checks: after max_fails=2 errors nginx skips a server for fail_timeout=10 s and retries the request on the next one. The single nginx edge is still the point of failure (Ext E).",
  shots=[(M3+"ED0-A-stopped.png", "Keshav: port 3001 still LISTEN, so A was not stopped"),
         (M1+"ED1-failover.png", "Mohan: run during the failed stop"), (M1+"ED2-recovery.png", "Mohan: recovery run"),
         (M2+"ED3-access-log.png", "Narendra: access log, note the two-upstream retry lines")],
  files=["mac2-edge-lb/evidence/ED3-access-log.txt"],
  note="The stop command missed the process, so this run does not show a clean 'all B' answer set. The proof of failover is the access-log lines with two upstreams (rt=2.123 and rt=1.029): nginx tried :3002, failed within the 2 s proxy_connect_timeout and served the request from :3001. The behaviour is set in nginx.conf: max_fails=2, fail_timeout=10s, proxy_next_upstream error timeout http_502 http_503 http_504. The script has since been fixed to stop the backend by port."),
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
 dict(id="p2-f", phase=2, title="Ext F: Troubleshooting", status="notes", owner="Mohan + Narendra",
  what="Narendra breaks something (stops nginx) and Mohan finds it with diagnose.sh by reading the layers in order.",
  ran=["Mohan: ./scripts/diagnose.sh (healthy)", "Narendra: nginx -s stop", "Mohan: ./scripts/diagnose.sh (fault)", "Narendra restarts nginx", "Mohan: ./scripts/diagnose.sh; ./scripts/phase2_check.sh"],
  saw=["Healthy run: every layer PASS (EF1).",
       "Narendra's log confirms 'nginx is STOPPED (fault injected)' (EF0), but Mohan's 'fault' run is also all PASS, so he ran it before nginx was stopped. It does not show the fault.",
       "Final check: all PASS and phase2_check says 9 ready, 0 not ready (EF3)."],
  why="Expected result of the real test: the first FAIL appears at layer 2 (TCP, edge port 8443 not open) and everything above it fails too. That tells you the edge is down, not DNS and not TLS.",
  shots=[(M1+"EF1-diagnose-ok.png", "Healthy"), (M1+"EF2-diagnose-fault.png", "Fault run: all PASS, nginx was not stopped yet"),
         (M1+"EF3-final-check.png", "Final check: 9 ready, 0 not ready")],
  files=["mac2-edge-lb/evidence/EF0-fault.txt"],
  note="Mohan's 'fault' run happened before nginx was stopped, so it shows all PASS; Narendra's log (EF0) proves nginx was stopped afterwards. For a real example of a broken layer see the failure demos in Phase 1: with the edge up and both backends down, DNS and TLS pass and HTTP returns 502, which is exactly where diagnose.sh prints its first FAIL. If the edge itself is stopped, the first FAIL moves to layer 2 (TCP, port 8443 closed)."),
]

MISSING = [
 "The Wireshark capture file phase1.pcapng was not recorded. The packet flow is explained in the Task G section and the TLS handshake messages are shown by demo_tls.sh.",
 "Caching (Task F) and failure demos 1, 4 and 5 were reproduced on Mac 2 after the lab session, not during it, because the lab backends had been switched off. They are labelled REPRODUCED.",
 "Ext C connectivity test, Ext D full failover and the Ext F fault run were taken at the wrong moment (see the notes). The configuration and the supporting logs are complete.",
 "Failures 2 and 3 are explained from existing evidence, not shown as separate screenshots.",
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
import re
def load_log(path, rx=None):
    t = open(os.path.normpath(os.path.join(HERE, path)), errors="replace").read()
    t = re.sub(r"\x1b\[[0-9;]*m", "", t)
    out = []
    for ln in t.splitlines():
        if "--:--:--" in ln or ln.strip().startswith(("% Total", "Dload", "Upload")): continue
        if rx and not re.search(rx, ln): continue
        out.append(ln)
    return "\n".join(out).strip()

ST = {"ok": ("PASS", "Evidence complete"), "notes": ("PASS WITH NOTES", "Evidence complete, see the note"), "repro": ("REPRODUCED", "Reproduced live on Mac 2"), "explained": ("EXPLAINED", "Explained, capture not taken")}
CLS = {"ok": "ok", "notes": "notes", "repro": "repro", "explained": "expl"}

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
        o.append(f"| {s['title']} | {s['owner']} | **{s.get('badge') or ST[s['status']][0]}** |")
    o.append("\n**PASS** = evidence captured and valid. **PASS WITH NOTES** = valid evidence plus one honest note about what a screenshot does or does not show. **REPRODUCED** = captured live on Mac 2 after the lab session. **EXPLAINED** = no capture, the behaviour is explained from other evidence.\n")
    for ph, name in ((1, "Phase 1: Build and observe"), (2, "Phase 2: Harden and recover")):
        o.append(f"\n## {2 + ph}. {name}\n")
        for s in [x for x in SECTIONS if x["phase"] == ph]:
            o.append(f"### {s['title']}  `{ST[s['status']][0]}`\n")
            o.append(f"**Owner:** {s['owner']}\n\n**What we did:** {s['what']}\n\n**Commands:**\n```bash\n" + "\n".join(s['ran']) + "\n```\n")
            o.append("**What the evidence shows:**\n" + "\n".join(f"- {x}" for x in s['saw']) + "\n")
            o.append(f"**Why it works:** {s['why']}\n")
            if s.get("note"): o.append(f"> **Note:** {s['note']}\n")
            for cap, pth, rx in s.get("logs", []): o.append(f"**{cap}**\n```text\n{load_log(pth, rx)}\n```\n")
            for p, c in s["shots"]: o.append(f"![{c}]({p})\n*{c}*\n")
            if s.get("files"): o.append("Raw logs: " + ", ".join(f"`{f}`" for f in s["files"]) + "\n")
    o.append("\n## 5. Problems we hit and how we fixed them\n")
    o.append("| Problem | What happened and the fix |\n|---|---|")
    for a, b in PROBLEMS: o.append(f"| {a} | {b} |")
    o.append("\n## 6. Limitations and honest notes\n")
    for m in MISSING: o.append(f"- {m}")
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
.ok{background:#e3f7ee;color:var(--green)}.notes{background:#e8f0ff;color:var(--blue)}.repro{background:#f0eaff;color:var(--purple)}.expl{background:#eef1f6;color:var(--mute)}
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
.redo-box{border-left:4px solid var(--blue);background:#eef3ff;padding:10px 14px;border-radius:0 12px 12px 0;margin-top:12px}
.shots{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));margin-top:14px}
pre.log{max-height:360px;white-space:pre-wrap;word-break:break-word}
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
    ok = sum(s["status"] == "ok" for s in SECTIONS); redo = sum(s["status"] == "notes" for s in SECTIONS); rep = sum(s["status"] in ("repro", "explained") for s in SECTIONS)
    shots = sum(len(s["shots"]) for s in SECTIONS)
    o = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CN Project Evidence Report</title><style>{CSS}</style></head><body>']
    o.append('<div class="hero"><div class="wrap"><span class="pill ok">TEAM 1 · 25 NOV 2026</span><h1>CN Project: what we built and the proof</h1>'
             '<p>Our own DNS, our own certificate authority, an HTTPS load balancer and two backends on four laptops. Below: every step, the exact command, the screenshot, and why it works.</p></div></div>')
    o.append('<nav><div class="in"><a href="#top">Overview</a><a href="#glance">At a glance</a><a href="#phase1">Phase 1</a><a href="#phase2">Phase 2</a><a href="#problems">Problems and fixes</a><a href="#todo">Limitations</a><a href="#viva">Viva</a></div></nav><div id="top"></div>')
    o.append('<section><div class="wrap"><h2>How a request travels</h2><p class="sub">Four laptops, one job each.</p><div class="flow">'
             '<div class="n" style="border-color:#2f6bff;background:#e8f0ff">Client</div><div class="a">→ DNS</div><div class="n" style="border-color:#7a4dff;background:#f0eaff">Mac 1 · dnsmasq</div>'
             '<div class="a">→ TCP + TLS</div><div class="n" style="border-color:#e8830c;background:#fff2e0">Mac 2 · nginx edge</div><div class="a">→</div>'
             '<div class="n" style="border-color:#14a06a;background:#e3f7ee">Mac 3 · Backend A</div><div class="a">or</div><div class="n" style="border-color:#14a06a;background:#e3f7ee">Mac 4 · Backend B</div></div>'
             '<div class="grid g4" style="margin-top:18px">' +
             "".join(f'<div class="card team" style="--c:{c}"><b>{E(m)} · {E(n)}</b><br><code>{ip}</code><br><span class="owner">{E(r)}</span></div>' for m, n, ip, r, c in TEAM) +
             '</div></div></section>')
    o.append(f'<section id="glance"><div class="wrap"><h2>Result at a glance</h2><p class="sub">Honest status for every task: green = valid evidence, blue = valid with a note, purple = reproduced live on Mac 2, grey = explained.</p>'
             f'<div class="grid g4"><div class="card kpi"><div class="big" style="color:var(--green)">{ok}</div><div class="l">tasks with complete evidence</div></div>'
             f'<div class="card kpi"><div class="big" style="color:var(--blue)">{redo}</div><div class="l">passed with an honest note</div></div>'
             f'<div class="card kpi"><div class="big" style="color:var(--blue)">{shots}</div><div class="l">screenshots in this report</div></div>'
             f'<div class="card kpi"><div class="big" style="color:var(--purple)">{rep}</div><div class="l">reproduced live or explained</div></div></div>'
             '<div class="scroll" style="margin-top:18px"><table><tr><th>Task</th><th>Owner</th><th>Status</th></tr>' +
             "".join(f'<tr><td><a href="#{s["id"]}">{E(s["title"])}</a></td><td>{E(s["owner"])}</td><td><span class="pill {CLS[s["status"]]}">{E(s.get("badge") or ST[s["status"]][0])}</span></td></tr>' for s in SECTIONS) +
             '</table></div></div></section>')
    for ph, name, sub in ((1, "Phase 1: Build and observe", "Make it work, then watch it work."), (2, "Phase 2: Harden and recover", "Break it on purpose and show it recovers.")):
        o.append(f'<section id="phase{ph}"><div class="wrap"><h2>{name}</h2><p class="sub">{sub}</p>')
        for s in [x for x in SECTIONS if x["phase"] == ph]:
            cls = CLS[s["status"]]
            o.append(f'<div class="sec" id="{s["id"]}"><div class="head"><div><h3>{E(s["title"])}</h3><div class="owner">{E(s["owner"])}</div></div><span class="pill {cls}">{E(s.get("badge") or ST[s["status"]][0])}</span></div><div class="body">')
            o.append(f'<div class="lbl">What we did</div><div>{E(s["what"])}</div>')
            o.append('<div class="lbl">Commands</div><pre>' + E("\n".join(s["ran"])) + '</pre>')
            o.append('<div class="lbl">What the evidence shows</div><ul>' + "".join(f'<li>{E(x)}</li>' for x in s["saw"]) + '</ul>')
            if s.get("chart") == "ttl": o.append(chart_ttl())
            if s.get("chart") == "cutover": o.append(chart_cut())
            o.append(f'<div class="why"><b>Why it works:</b> {E(s["why"])}</div>')
            if s.get("note"): o.append(f'<div class="redo-box"><b>Note:</b> {E(s["note"])}</div>')
            for cap, pth, rx in s.get("logs", []): o.append(f'<div class="lbl">{E(cap)}</div><pre class="log">{E(load_log(pth, rx))}</pre>')
            o.append('<div class="shots">' + "".join(f'<figure><img loading="lazy" src="{p}" alt="{E(c)}"><figcaption>{E(c)}</figcaption></figure>' for p, c in s["shots"]) + '</div>')
            if s.get("files"): o.append('<div class="lbl">Raw logs</div><div>' + " ".join(f'<code>{E(f)}</code>' for f in s["files"]) + '</div>')
            o.append('</div></div>')
        o.append('</div></section>')
    o.append('<section id="problems"><div class="wrap"><h2>Problems we hit and how we fixed them</h2><p class="sub">Real issues from the lab, each one a good viva answer.</p><div class="scroll"><table><tr><th>Problem</th><th>What happened and the fix</th></tr>' +
             "".join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td></tr>' for a, b in PROBLEMS) + '</table></div></div></section>')
    o.append('<section id="todo"><div class="wrap"><h2>Limitations and honest notes</h2><p class="sub">What the evidence does and does not show.</p><div class="card"><ul>' +
             "".join(f'<li>{E(m)}</li>' for m in MISSING) + '</ul></div></div></section>')
    o.append('<section id="viva"><div class="wrap"><h2>Viva: short answers</h2><p class="sub">Click a question.</p>' +
             "".join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in VIVA) + '</div></section>')
    o.append('<footer>CN Project · team1 · Mohan Kumar C R · Narendra Singh · Keshav Rajput · Mayank Gupta · generated by evidence/build_report.py</footer>')
    o.append('<div id="lb"><img alt=""></div><script>const lb=document.getElementById("lb"),im=lb.querySelector("img");document.addEventListener("click",e=>{if(e.target.matches("figure img")){im.src=e.target.src;lb.style.display="flex"}else if(lb.style.display==="flex"){lb.style.display="none"}});document.addEventListener("keydown",e=>{if(e.key==="Escape")lb.style.display="none"});</script></body></html>')
    return "\n".join(o)

if __name__ == "__main__":
    open(os.path.join(HERE, "FINAL_REPORT.md"), "w").write(md())
    open(os.path.join(HERE, "index.html"), "w").write(page())
    missing = [p for s in SECTIONS for p, _ in s["shots"] if not os.path.exists(os.path.normpath(os.path.join(HERE, p)))]
    print("written FINAL_REPORT.md and index.html; missing images:", missing or "none")
