# Mac 2 — Edge Reverse Proxy + Load Balancer + TLS  (THIS laptop)

**Role:** the only entry point. DNS names point here; nginx terminates TLS (port 8443) and round-robins to Backend A (Mac 3 :3001) and Backend B (Mac 4 :3002). Cloud equivalent: AWS ALB / CDN edge. You also own the **CA** (Task E).

## Step 0 — Get the code (every teammate, on their own Mac)
```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren      # first time only
cd ~/CN-Project-Naren && git pull               # every time before you start (picks up IP/config changes)
cd mac2-edge-lb
```
Then continue with Phase 1 below. If `./scripts/...` says "permission denied": `chmod +x scripts/*.sh backend/*.sh 2>/dev/null`.
If your Mac's IP differs from `team.env`, tell the team (one person edits `team.env`, runs `./sync.sh`, commits and pushes; everyone else runs `git pull`).

(On Narendra's laptop the repo is at `/Users/Narendra/Desktop/NST/CN Project` — just `cd` into `mac2-edge-lb`.)

## Phase 1

### Task A — LAN
```bash
./scripts/check_lan.sh            # IP, mask, gateway, MAC + ping all Macs → fill IP table
```
Also useful: `ipconfig getifaddr en0` · `networksetup -listallhardwareports`

### Task D+E — nginx + TLS (do after both backends are running, DNS can come later)
```bash
brew install nginx                # if you get HTTP/2 warnings: brew uninstall nginx-full && brew install nginx
./scripts/make_certs.sh           # creates certs/ (CA + app cert with SAN app.team1.test, api.team1.test)
./scripts/configure_nginx.sh      # renders generated/nginx.conf → brew etc/nginx, nginx -t, starts/reloads
```
Check:
```bash
lsof -nP -iTCP:8443 -sTCP:LISTEN
curl -s http://MAC3_IP:3001/health ; curl -s http://MAC4_IP:3002/health      # edge can reach backends
tail -f "$(brew --prefix)/var/log/nginx/access.log"                          # shows backend=… xb=A/B per request
```
> This laptop's nginx is `nginx-full` without the HTTP/2 module. The script auto-detects and serves HTTP/1.1; install the standard `nginx` formula if you want to show HTTP/2 (optional per brief).

### Distribute the CA to every client (Task E)
```bash
./scripts/serve_ca.sh             # leave running; on Mac 1/3/4 run ./scripts/trust_ca.sh ; then Ctrl+C here
```
Only `public/ca.crt` is served; private keys stay in `certs/`. Without the CA, `curl` exits 60 (verified).

### Use this Mac as a client too (optional but good for evidence)
```bash
./scripts/trust_ca.sh /absolute/path/to/certs/ca.crt   # or the one-liner above, after set_dns
./scripts/set_dns.sh primary
./scripts/demo_lb.sh
```

### Control
```bash
nginx -t ; nginx -s reload ; nginx -s stop ; pgrep -x nginx
```
(Ports 8443/8080 need no sudo.)

## Phase 2 duties
- **Ext D (HA failover):** already in the config (`max_fails=2 fail_timeout=10s`, `proxy_next_upstream`). Stop Backend A on Mac 3 → all answers `X-Backend: B`; restart → A/B again. Explain SPOF = this nginx.
- **Ext E (migration):** this edge returns `X-Edge: mac2`; the standby on Mac 3 returns `X-Edge: standby`. After DNS cutover, optionally `nginx -s stop` here and show the service survives.
- **Ext C test:** after Mac 3/4 enable pf, prove from here `curl http://MAC3_IP:3001/health` still works, while Mac 1 gets a timeout.
- Backups for the standby: copy `certs/app.crt` and `certs/app.key` to Mac 3 (`scp certs/app.* USER@MAC3_IP:~/cn/mac3-backend-a/certs/`).
- Config bundle: `generated/nginx.conf`, `scripts/`, certificate notes (`make_certs.sh`).

## Evidence you own
`nginx -t` OK · `generated/nginx.conf` · `openssl x509 -text` SAN output · `openssl verify` OK · access.log showing alternating `xb=A/B` · `lsof` showing LISTEN · pf test from this Mac.

## Be ready to explain (viva)
Reverse proxy vs load balancer · round-robin vs least_conn vs ip_hash · L7 vs L4 · why clients never need backend IPs · TLS termination + risks of plain HTTP to backends · chain of trust, SAN, SNI · passive health checks (active = nginx Plus) · single point of failure and how to remove it.
