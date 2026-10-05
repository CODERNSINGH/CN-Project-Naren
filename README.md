# CN Project — Private Network Service Platform (team1)

A client types `https://app.team1.test:8443`, the name is resolved by **our own DNS server**, the request reaches an **nginx HTTPS edge / load balancer**, and is answered by one of **two backends** — all on our own laptops, no cloud.

```
Client ─(1) DNS UDP/53─► Mac 1 dnsmasq        ─(2) A record = Mac 2 IP
Client ─(3) TCP + (4) TLS ─► Mac 2 nginx :8443 ──(6)──► Mac 3 Backend A :3001
                                                └──(6)──► Mac 4 Backend B :3002      X-Backend: A / B
```
Full picture: open **`CN_Project_Architecture.excalidraw`** at https://excalidraw.com (Open / drag & drop, Shift+1 to fit).
Source documents: `Docs/` (brief + master PDF).

## 1. Team, network and IPs (verified 2026-10-05)

Campus Wi-Fi **10.7.0.0/19** · netmask `255.255.224.0` · router/gateway `10.7.0.1` (**never use the router as a Mac IP**) · DHCP server `10.1.0.2`. All four Macs are in the same subnet and answer ping from each other (no client isolation).

| Mac | Owner | Role | IP | Folder |
|---|---|---|---|---|
| 1 | Mohan | DNS server (dnsmasq) + **test client** | `10.7.16.221` | `mac1-dns-client/` |
| 2 | Narendra | **Edge**: nginx reverse proxy + load balancer + TLS + CA | `10.7.2.91` | `mac2-edge-lb/` |
| 3 | Keshav | **Backend A** `:3001` (+ backup DNS, standby edge in Phase 2) | `10.7.1.186` | `mac3-backend-a/` |
| 4 | Mayank | **Backend B** `:3002` | `10.7.8.104` | `mac4-backend-b/` |

The single source of truth is **`team.env`**. If a Mac's IP changes (DHCP), see §6.

## 2. Status

| Item | State |
|---|---|
| Mac 2: CA + server certificate (SAN `app.team1.test`, `api.team1.test`) | ✅ done |
| Mac 2: nginx running on `:8443` (HTTPS) and `:8080` (redirect), upstream = Mac 3 + Mac 4 | ✅ running |
| Mac 2: TLS verified (`SSL certificate verify ok`, TLS 1.3) | ✅ |
| Mac 3 / Mac 4 backends | ⏳ Keshav / Mayank start them (§3) |
| Mac 1 dnsmasq + trust CA + set DNS | ⏳ Mohan (§3) |
| Phase 1 gate (`demo_lb.sh` alternates A,B) | ⏳ after the three above |

Until the backends run, the edge answers **502 Bad Gateway** — that is expected (it is Failure demo #4).

## 3. What each person runs RIGHT NOW (copy-paste)

**Everyone, first time:**
```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren
cd ~/CN-Project-Naren && git pull
```
Needs: Homebrew (https://brew.sh), Python 3, admin password. If a pop-up asks "accept incoming connections?" → **Allow**.

### Keshav — Mac 3, Backend A
```bash
cd ~/CN-Project-Naren/mac3-backend-a
./scripts/my_ip.sh                  # must print 10.7.1.186
./backend/run_backend.sh            # leave this terminal open: "Running on http://0.0.0.0:3001"
# in a 2nd terminal:
curl -i http://10.7.1.186:3001/api/status      # {"backend":"A",...} + header X-Backend: A
```
### Mayank — Mac 4, Backend B
```bash
cd ~/CN-Project-Naren/mac4-backend-b
./scripts/my_ip.sh                  # must print 10.7.8.104
./backend/run_backend.sh            # leave open: "Running on http://0.0.0.0:3002"
curl -i http://10.7.8.104:3002/api/status      # X-Backend: B
```
> Mayank's last output showed `ping: No route to host` to the router → his Wi-Fi dropped for a moment. Re-join the Wi-Fi and re-run `./scripts/my_ip.sh`; the ping to the router must succeed.

### Mohan — Mac 1, DNS + client
**Turn off Cloudflare WARP / any VPN / DNS-filter app first** — Mohan's DNS showed `127.0.2.2`, a local DNS proxy that would ignore our server (the scripts print a red WARNING if it is still on).
```bash
cd ~/CN-Project-Naren/mac1-dns-client
./scripts/my_ip.sh                  # must print 10.7.16.221
./scripts/setup_dnsmasq.sh primary  # installs + starts dnsmasq; last lines must show 10.7.2.91
```
Then, once Narendra says "CA is being served":
```bash
./scripts/trust_ca.sh               # downloads + trusts the team CA
./scripts/set_dns.sh primary        # this Mac now resolves through itself (old DNS is saved, restore: ./scripts/set_dns.sh restore)
dig app.team1.test                  # ANSWER: 10.7.2.91
./scripts/demo_lb.sh                # PHASE 1 GATE: X-Backend alternates A,B,A,B
```

### Narendra — Mac 2, edge (already built; to re-run / serve the CA)
```bash
cd "/Users/Narendra/Desktop/NST/CN Project/mac2-edge-lb"
./scripts/serve_ca.sh               # leave running until Mohan, Keshav, Mayank have run trust_ca.sh, then Ctrl+C
nginx -t ; nginx -s reload          # after any config change
tail -f /opt/homebrew/var/log/nginx/access.log     # shows backend=… xb=A/B for every request
```

### Keshav + Mayank — also act as clients (needed: ≥2 clients using our DNS)
```bash
./scripts/trust_ca.sh && ./scripts/set_dns.sh primary
dig app.team1.test && ./scripts/demo_lb.sh
```

## 4. After the gate — the rest of the project (details in each Mac README)

| Step | Who | Command | Evidence |
|---|---|---|---|
| Caching (Task F) | Mohan | `./scripts/demo_cache.sh` | Cache-Control, ETag, 304 |
| TLS proof (Task E) | Mohan | `./scripts/demo_tls.sh` | verify return code 0 |
| Wireshark (Task G) | Mohan | see `mac1-dns-client/README.md` | `phase1.pcapng`, `tls12.pcapng` |
| 5 failure demos | Mohan (+Keshav for #3) | `./scripts/failures.sh 1..5` | screenshots |
| Backup DNS (Ext A) | Keshav | `./scripts/setup_dnsmasq.sh backup` | `dig @10.7.1.186` |
| TTL (Ext B) | Mohan | `TTL=30 ./scripts/setup_dnsmasq.sh primary` + `demo_ttl.sh` | timeline |
| Isolation (Ext C) | Keshav, Mayank | `./scripts/isolate_pf.sh 3001` / `3002` … `rollback_pf.sh` | blocked vs allowed |
| HA failover (Ext D) | Keshav | stop/start Backend A | all B, then A/B |
| Edge migration (Ext E) | Keshav + Mohan | `./scripts/configure_nginx.sh standby` + `demo_edge.sh` | X-Edge flips |
| Troubleshooting (Ext F) | all | `./scripts/diagnose.sh` | layered output |

Then: `DEMO_RUNBOOK.md` (the 11 evaluation steps), `EVIDENCE_CHECKLIST.md` (what to save), `VIDEO_SCRIPT.md` (submission video), `GUIDE_END_TO_END.md` (how everything works, environment, troubleshooting).

## 5. Golden rules
- No `curl -k`, no IP in the URL, domain is `.test` (never `.local`).
- Ports: HTTPS **8443**, redirect **8080**, backends **3001/3002**, DNS **53**.
- Run every script from inside **your own Mac's folder** (`./scripts/…`). Each script refuses to run if the IP in `team.env` is not this Mac's IP — that means someone's DHCP address changed (§6).
- When something breaks: `./scripts/diagnose.sh` on a client, read the **first FAIL** (IP → DNS → TCP → TLS → HTTP → backends).
- Never commit private keys — `certs/`, `generated/`, `venv/`, `dist/`, `*.pcap*` are git-ignored.
- Keep Macs awake during the demo: `caffeinate -d`.

## 6. If an IP changes (campus DHCP can renew)
```bash
./scripts/my_ip.sh                                  # on the Mac whose IP changed → tell Narendra
# Narendra:
cd "/Users/Narendra/Desktop/NST/CN Project"
./setup_team.sh <MAC1_IP> <MAC2_IP> <MAC3_IP> <MAC4_IP> team1
git add -A && git commit -m "update IPs" && git push
# everyone: git pull ; then re-run the step that uses the IP:
#   Mac 1 → ./scripts/setup_dnsmasq.sh primary      Mac 2 → ./scripts/configure_nginx.sh
```
If Mac 2's IP changes, certificates stay valid (they contain names, not IPs). If the campus Wi-Fi ever blocks Mac-to-Mac traffic, use one phone hotspot for all four Macs.

## 7. Repository layout
```
team.env  setup_team.sh  sync.sh          ← IPs + helpers (edit via setup_team.sh, then push)
_shared/{common,mac2,backend,diagram}     ← single source of truth for scripts, backend, diagram generator
mac1-dns-client/  mac2-edge-lb/  mac3-backend-a/  mac4-backend-b/    ← per-laptop README + scripts (+ backend/)
CN_Project_Architecture.excalidraw  GUIDE_END_TO_END.md  DEMO_RUNBOOK.md  EVIDENCE_CHECKLIST.md  VIDEO_SCRIPT.md
Docs/  evidence/
```
Edit `_shared/…` then run `./sync.sh` (copies into the four folders). Regenerate the diagram: `python3 _shared/diagram/build_excalidraw.py`.

Deliverables map: Architecture doc = diagram + `Docs/CN_Project_Master.pdf` · Configuration bundle = each Mac's `generated/*.conf` + `scripts/` · Backend code = `_shared/backend/` · Evidence = `evidence/` · Phase 2 report = master PDF ch. 9 · Video = `VIDEO_SCRIPT.md`.
