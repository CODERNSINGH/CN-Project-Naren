# CN Project — Private Network Service Platform (team1)

End-to-end build: **Client → DNS (Mac 1) → HTTPS/nginx LB (Mac 2) → Backend A (Mac 3) / Backend B (Mac 4)**.
Source documents are in `Docs/`. Everything below is already coded and tested locally (round-robin, TLS, 304, failover, 502).

| Folder | Mac | Role | Your instructions |
|---|---|---|---|
| `mac1-dns-client/` | Mac 1 | dnsmasq DNS server + **test client** (Wireshark, demos) | `mac1-dns-client/README.md` |
| `mac2-edge-lb/` | **Mac 2 = THIS laptop** | nginx reverse proxy, load balancer, TLS, CA | `mac2-edge-lb/README.md` |
| `mac3-backend-a/` | Mac 3 | Backend A `:3001`, backup DNS, standby edge | `mac3-backend-a/README.md` |
| `mac4-backend-b/` | Mac 4 | Backend B `:3002` | `mac4-backend-b/README.md` |

Also: **`GUIDE_END_TO_END.md`** (how it works, environment per Mac, IP commands, who does what, troubleshooting), **`VIDEO_SCRIPT.md`** (submission video plan), `DEMO_RUNBOOK.md` (the 11 evaluation steps → exact commands), `EVIDENCE_CHECKLIST.md` (what to screenshot/save).

## 0. One-time prep (on THIS laptop)
1. Connect all 4 Macs to the **same Wi-Fi / hotspot** (VPN off; no "AP isolation").
2. On every Mac find its IP: `ipconfig getifaddr en0`
3. Each Mac runs `./scripts/my_ip.sh` to get its IP. Then edit **`team.env`** — or simply run `./setup_team.sh IP1 IP2 IP3 IP4 team1` (writes it and syncs). To sync by hand:
   ```bash
   cd "/Users/Narendra/Desktop/NST/CN Project" && ./sync.sh
   ```
   This copies `team.env` + scripts into every Mac folder and writes `dist/mac1-dns-client.zip … mac4-backend-b.zip`.
   **Re-run `./sync.sh` after any edit to `team.env` or `_shared/`.**
4. Commit + push so teammates get it (see section 4). Each teammate then does, on their own Mac:
   ```bash
   git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren && cd ~/CN-Project-Naren/<their-folder>   # e.g. mac3-backend-a
   ```
   and re-runs `git pull` whenever `team.env` changes. (Zips in `dist/` still work for AirDrop/USB if there is no internet.)
5. Every Mac needs Homebrew (https://brew.sh) and an admin account.

## 1. Build order (follow exactly — each step says which Mac)

| # | Mac | Command(s) | Success looks like |
|---|---|---|---|
| 1 | all | `./scripts/check_lan.sh` | all four `OK` in the ping matrix → fill the IP table |
| 2 | 3 | `./backend/run_backend.sh` *(leave running)* | `Running on http://0.0.0.0:3001` |
| 3 | 4 | `./backend/run_backend.sh` *(leave running)* | `Running on http://0.0.0.0:3002` |
| 4 | 1 | `curl -i http://MAC3_IP:3001/api/status` and `…MAC4_IP:3002…` | JSON + `X-Backend: A/B` from another Mac |
| 5 | 1 | `./scripts/setup_dnsmasq.sh primary` | `dig` prints Mac 2's IP |
| 6 | 2 | `brew install nginx` then `./scripts/make_certs.sh` | `app.crt: OK` |
| 7 | 2 | `./scripts/configure_nginx.sh` | `nginx -t` ok, port 8443 LISTEN |
| 8 | 2 | `./scripts/serve_ca.sh` *(leave running a minute)* | serves `http://MAC2_IP:8000/ca.crt` |
| 9 | 1, 3, 4 | `./scripts/trust_ca.sh` then `./scripts/set_dns.sh primary` | no cert warnings; name resolves |
| 10 | 1 | `./scripts/demo_lb.sh` | `X-Backend` alternates A, B, A, B … **Phase 1 gate passed** |
| 11 | 1 | `demo_cache.sh`, `demo_tls.sh`, `capture.sh`, `failures.sh 1..5` | Tasks E, F, G + five failure demos |
| 12 | 3 | Phase 2 → `mac3-backend-a/README.md` (backup DNS, standby edge) | Ext A, E |
| 13 | 3, 4 | `./scripts/isolate_pf.sh PORT` / `rollback_pf.sh` | Ext C |
| 14 | 1 | `./scripts/diagnose.sh` | layered troubleshooting (Ext F) |

Ports: HTTPS **8443**, HTTP redirect **8080** (allowed by the brief). So URLs are `https://app.team1.test:8443/…`.

## 2. Golden rules
- Never use `curl -k` in the demo; never type an IP in the URL.
- Never use `.local`; the domain is `.test`.
- Mac 2's IP must be the **same** in `team.env`, dnsmasq (`app.team1.test → MAC2_IP`) and the certificate names (names, not IPs).
- If something breaks, run `./scripts/diagnose.sh` on a client and read the **first FAIL** (IP → DNS → TCP → TLS → HTTP → backends).
- macOS pop-ups "Do you want python/nginx/dnsmasq to accept incoming connections?" → **Allow**.
- Keep laptops awake during the demo: `caffeinate -d`.

## 3. Layout
```
team.env  sync.sh  dist/  Docs/  evidence/
_shared/{common,mac2,backend}   ← single source of truth (edit here, then ./sync.sh)
mac1-dns-client/  mac2-edge-lb/  mac3-backend-a/  mac4-backend-b/   ← self-contained per laptop
```
Deliverables mapping: Architecture doc = `Docs/CN_Project_Master.pdf` + your IP table · Config bundle = each Mac's `generated/` folder (dnsmasq.conf, nginx.conf) + `scripts/` · Backend code = `_shared/backend/` · Evidence = `evidence/` (see checklist).

## 4. Git workflow (GitHub: CODERNSINGH/CN-Project-Naren)
```bash
# whoever changes team.env or _shared/:
./sync.sh && git add -A && git commit -m "update config" && git push
# everyone else:
git pull
```
Never commit private keys: `.gitignore` already excludes `certs/`, `generated/`, `venv/`, `dist/`, `*.pcap*`. Evidence screenshots go in `evidence/` (those ARE committed).
