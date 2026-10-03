# End-to-End Guide — environment, per-Mac tasks, and how it all works

## 1. How the system works (read this first — everyone must be able to explain it)

```
                 ┌──────────── same Wi-Fi / hotspot (one subnet) ────────────┐
 Mac 1 (client)  │                                                           │
  browser/curl ──┼─(1) DNS query UDP/53 "app.team1.test?" ──► Mac 1 dnsmasq  │
                 │◄─(2) answer: A record = Mac 2 IP (TTL) ───────────────────│
                 ├─(3) TCP SYN/SYN-ACK/ACK to Mac 2 :8443                    │
                 ├─(4) TLS handshake (cert for app.team1.test, signed by    │
                 │      our team CA that every Mac trusts)                  │
                 ├─(5) HTTP request, encrypted in TLS ─► Mac 2 nginx         │
                 │                      │ terminates TLS, picks backend      │
                 │                      ├─(6) plain HTTP ► Mac 3 :3001 (A)  │
                 │                      └─(6) plain HTTP ► Mac 4 :3002 (B)  │
                 │◄─(7) JSON + X-Backend: A|B + X-Edge: mac2 ─────────────────│
```
1. **DNS** finds an IP only (dnsmasq on Mac 1 = "Route 53"). It never connects to anything.
2. **TCP** gives a reliable connection (3-way handshake, sequence/ACK numbers, ports: client ephemeral → 8443).
3. **TLS** authenticates the server (certificate → CA chain → SAN must match hostname) and encrypts. Terminated at nginx.
4. **HTTP/REST** is the application. `Cache-Control`/`ETag` allow caching and `304 Not Modified`.
5. **Load balancing:** nginx round-robins A, B, A, B. Clients never know backend IPs.
6. **Resilience (Phase 2):** backup DNS, TTL/cutover, pf isolation, passive health-check failover, standby edge.

Machine ↔ cloud: dnsmasq = Route 53 · nginx = ALB/CDN edge · backends = EC2 · pf = security groups · DNS cutover = Route 53 failover.

## 2. Environment each Mac needs (do this BEFORE the lab)

| Need | Mac 1 | Mac 2 | Mac 3 | Mac 4 |
|---|---|---|---|---|
| Admin account (sudo) | ✔ | ✔ | ✔ | ✔ |
| Homebrew (https://brew.sh) | ✔ | ✔ | ✔ | ✔ |
| git (`xcode-select --install`) | ✔ | ✔ | ✔ | ✔ |
| Python 3 (`python3 --version`) | – | – | ✔ | ✔ |
| `brew install dnsmasq` | ✔ (script does it) | – | ✔ backup DNS | – |
| `brew install nginx` | – | ✔ | ✔ standby edge | – |
| Wireshark (`brew install --cask wireshark`) | ✔ | optional | – | – |
| Flask | – | – | auto (venv) | auto (venv) |

Network rules: all Macs on the **same** Wi-Fi/hotspot · VPN off · iCloud Private Relay off · router "AP/client isolation" off (if Macs can't ping each other, use a phone hotspot) · allow incoming-connection pop-ups for python/nginx/dnsmasq · keep Macs awake (`caffeinate -d`).

## 3. Getting IP address and network info (every Mac)

```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren
cd ~/CN-Project-Naren/<your-folder>
./scripts/my_ip.sh             # one command: IP, netmask, gateway, MAC, interface, DNS, Wi-Fi name
```
Manual equivalents (for screenshots / viva):
```bash
ipconfig getifaddr en0                         # your IPv4 (use en1 if en0 is empty)
ifconfig en0 | grep -E "inet |ether"           # IPv4, netmask (hex 0xffffff00 = 255.255.255.0 = /24), MAC
netstat -nr | grep default                     # default gateway
networksetup -listallhardwareports             # interface name + service name ("Wi-Fi")
networksetup -getdnsservers Wi-Fi              # configured DNS
scutil --dns | head -30                        # resolver actually in use
arp -a                                         # other Macs seen on the LAN (shows MACs)
ping -c 4 <other-mac-ip>                       # reachability
```
**Team lead (Narendra, Mac 2)** collects the four IPs, then on this laptop:
```bash
cd "/Users/Narendra/Desktop/NST/CN Project"
./setup_team.sh <MAC1_IP> <MAC2_IP> <MAC3_IP> <MAC4_IP> team1   # writes team.env + copies into all folders
git add -A && git commit -m "set team IPs" && git push
```
Everyone else: `cd ~/CN-Project-Naren && git pull`. (If an IP changes later — Wi-Fi reconnects can change it — re-run `setup_team.sh`, push, pull. Tip: set a DHCP reservation in the router or a "Manual IP" in System Settings → Network so IPs stay fixed during the demo.)
Record the final table (fill in from `my_ip.sh`):

| Mac | Role | IPv4 | Mask | Gateway | Iface | MAC addr |
|---|---|---|---|---|---|---|
| 1 | DNS + client | | | | en0 | |
| 2 | Edge/LB/TLS | | | | en0 | |
| 3 | Backend A | | | | en0 | |
| 4 | Backend B | | | | en0 | |

## 4. What each person does (checklist, in time order)

### Everyone
1. Join the shared network → `./scripts/my_ip.sh` → send IP to team lead → `git pull` after team.env is pushed.
2. `./scripts/check_lan.sh` → every line `OK` (Task A evidence: screenshot).

### Mac 3 — Backend A (start first)
`./backend/run_backend.sh` (leave open) → from another Mac `curl -i http://MAC3_IP:3001/api/status` shows `X-Backend: A`.

### Mac 4 — Backend B
`./backend/run_backend.sh` (leave open) → `curl -i http://MAC4_IP:3002/api/status` shows `X-Backend: B`.

### Mac 1 — DNS
`./scripts/setup_dnsmasq.sh primary` → `./scripts/set_dns.sh primary` → `dig app.team1.test` returns Mac 2's IP.

### Mac 2 — Edge (this laptop)
`brew install nginx` → `./scripts/make_certs.sh` → `./scripts/configure_nginx.sh` → `./scripts/serve_ca.sh` (leave running while others trust the CA).

### Mac 1, 3, 4 — trust CA + DNS (≥2 clients required)
`./scripts/trust_ca.sh` and `./scripts/set_dns.sh primary` → `curl -sI https://app.team1.test:8443/api/status` works with no `-k`.

### Mac 1 — Phase 1 proof
`./scripts/demo_lb.sh` · `demo_cache.sh` · `demo_tls.sh` · Wireshark capture (see `mac1-dns-client/README.md`) · `failures.sh 1..5`.

### Phase 2 split
- Mac 3: backup DNS, standby edge, pf isolation (3001). Mac 4: pf isolation (3002). Mac 1: TTL + cutover + `diagnose.sh`. Mac 2: failover explanation, pf test from edge.

## 5. Verification table (what "working" looks like)

| Check | Command (from Mac 1) | Expected |
|---|---|---|
| LAN | `./scripts/check_lan.sh` | all OK |
| DNS | `dig +short app.team1.test` | Mac 2 IP |
| TCP | `nc -vz MAC2_IP 8443` | succeeded |
| TLS | `./scripts/demo_tls.sh` | `Verify return code: 0 (ok)` |
| App | `curl -si https://app.team1.test:8443/api/status` | 200, JSON, `X-Backend`, `X-Edge` |
| LB | `./scripts/demo_lb.sh` | A,B,A,B |
| Cache | `./scripts/demo_cache.sh` | `Cache-Control`, `ETag`, 304 |
| All layers | `./scripts/diagnose.sh` | all PASS |

## 6. Common problems
| Symptom | Cause / fix |
|---|---|
| `ping` fails between Macs | different Wi-Fi, VPN on, AP isolation → use hotspot |
| `dig` timeout | dnsmasq not running / client DNS wrong → `./scripts/set_dns.sh primary`; Mac 1 `sudo brew services restart dnsmasq`; check `tail /tmp/dnsmasq.log` |
| `curl` works with IP but not name | DNS cache → `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` |
| cert warning / curl exit 60 | CA not trusted on that Mac → `./scripts/trust_ca.sh`; Homebrew curl needs `--cacert ca.crt` |
| 502 Bad Gateway | backend stopped, wrong IP in `team.env`, or pf blocking Mac 2 → `diagnose.sh`, `tail error.log` |
| "address already in use" 8443/53 | another process: `sudo lsof -nP -iTCP:8443 -sTCP:LISTEN` |
| `setup_dnsmasq.sh`: "does not have IP" | wrong team.env IP, or run on wrong Mac → fix + `git pull` |
| IP changed after reconnect | `./setup_team.sh …` again, push, everyone pulls, re-run `setup_dnsmasq.sh`/`configure_nginx.sh` |
| pf left on after demo | `./scripts/rollback_pf.sh` |
| DNS broken on a Mac after demo | `./scripts/set_dns.sh reset` |

## 7. Cleanup after the project
`./scripts/set_dns.sh reset` · Mac 1/3 `sudo brew services stop dnsmasq` · Mac 2 `nginx -s stop` · `./scripts/rollback_pf.sh` · remove CA: Keychain Access → System → delete "team1 Local CA".
