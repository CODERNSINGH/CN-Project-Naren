# Mac 3 — Backend A (:3001) + Backup DNS + Standby Edge

**Role:** application server instance A (`X-Backend: A`). In Phase 2 this Mac also hosts the **backup DNS** (Ext A) and the **standby nginx** (Ext E).

## Step 0 — Get the code (every teammate, on their own Mac)
```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren      # first time only
cd ~/CN-Project-Naren && git pull               # every time before you start (picks up IP/config changes)
cd mac3-backend-a
```
Then continue with Phase 1 below. If `./scripts/...` says "permission denied": `chmod +x scripts/*.sh backend/*.sh 2>/dev/null`.
If your Mac's IP differs from `team.env`, tell the team (one person edits `team.env`, runs `./sync.sh`, commits and pushes; everyone else runs `git pull`).

## Phase 1

### Task A
```bash
./scripts/check_lan.sh
```

### Task C — run Backend A
```bash
./backend/run_backend.sh        # creates venv, installs Flask, binds 0.0.0.0:3001. Leave this terminal open.
```
Verify (second terminal here, and **from another Mac**):
```bash
curl -i http://MAC3_IP:3001/api/status           # {"backend":"A",…} + header X-Backend: A
curl -i http://MAC3_IP:3001/api/catalog          # Cache-Control: max-age=60 + ETag
lsof -nP -iTCP:3001 -sTCP:LISTEN                 # must show *:3001 (NOT 127.0.0.1)
```
Endpoints: `/` · `/api/status` (no-store) · `/api/catalog` (cacheable, ETag) · `/health`.
Click "Allow" on the macOS incoming-connection pop-up for Python.

### Also: be a client
`./scripts/trust_ca.sh` and `./scripts/set_dns.sh primary` (counts as one of the "two clients resolving via team DNS").

### Failure 3 / demo step 8
Stop this backend with **Ctrl+C**; the edge must keep serving via Backend B. Restart with `./backend/run_backend.sh`; load balancing resumes after ≤10 s (`fail_timeout`).

## Phase 2

### Ext A — Backup DNS resolver (this Mac)
```bash
./scripts/setup_dnsmasq.sh backup      # listens on BACKUP_DNS_IP (= this Mac) with the same records
dig +short app.team1.test @MAC3_IP     # → MAC2_IP
```
Keep records identical to Mac 1 during experiments (`TTL=30 APP_IP=… ./scripts/setup_dnsmasq.sh backup`).

### Ext C — Service isolation (pf)
```bash
./scripts/isolate_pf.sh 3001           # only Mac 2 may reach :3001 (backs up /etc/pf.conf first)
```
Demonstrate:
```bash
# from Mac 2:   curl -i http://MAC3_IP:3001/health          → 200
# from Mac 1:   curl -m 5 -i http://MAC3_IP:3001/health      → times out
#               nc -vz -w 3 MAC3_IP 3001                     → fails
#               curl -s https://app.team1.test:8443/api/status   → still works (via the edge)
./scripts/rollback_pf.sh               # ALWAYS restore after the demo → "rollback OK"
```
`drop` = silent timeout; `return` would reset instantly. Source-IP rules can be spoofed on a shared LAN — concept demo, not strong security.

### Ext E — Standby edge (this Mac)
1. On Mac 2 copy the certs here (names, not IPs, are in the cert so it is valid on this Mac too):
   `scp certs/app.crt certs/app.key USER@MAC3_IP:~/cn/mac3-backend-a/certs/` (create `certs/` first: `mkdir -p ~/cn/mac3-backend-a/certs`) — or AirDrop.
2. ```bash
   brew install nginx
   ./scripts/configure_nginx.sh standby     # X-Edge: standby on :8443 (backend stays on :3001, no conflict)
   curl --resolve app.team1.test:8443:MAC3_IP https://app.team1.test:8443/api/status   # verify the standby directly
   ```
3. If pf isolation is on, Mac 4's pf must also allow this standby: on Mac 4 `EXTRA_ALLOW=MAC3_IP ./scripts/isolate_pf.sh 3002` (and here the local-loopback rule is already included).
4. Cutover from Mac 1: `TTL=30 APP_IP=MAC3_IP ./scripts/setup_dnsmasq.sh primary` → watch `./scripts/demo_edge.sh`.

## Be ready to explain (viva)
Why bind 0.0.0.0 vs 127.0.0.1 · socket = IP+port+protocol · why different ports · what pf rules do (L3/L4, drop vs reject) · least privilege / cloud security groups · why the standby uses the same cert · TTL effects during cutover.
