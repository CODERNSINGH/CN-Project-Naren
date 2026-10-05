# Mac 4 — Backend B (:3002)

**Owner:** Mayank · **IP:** 10.7.8.104 · netmask 255.255.224.0 · gateway 10.7.0.1 (campus Wi-Fi, subnet 10.7.0.0/19) · all IPs: `../team.env`

**Role:** application server instance B (`X-Backend: B`).

## Step 0 — Get the code (every teammate, on their own Mac)
```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren      # first time only
cd ~/CN-Project-Naren && git pull               # every time before you start (picks up IP/config changes)
cd mac4-backend-b
```
**Step 0b — find your IP (send it to the team lead):** `./scripts/my_ip.sh` (full explanation + manual commands: `../GUIDE_END_TO_END.md` §3). Then `git pull` once the lead has pushed `team.env`.
Then continue with Phase 1 below. If `./scripts/...` says "permission denied": `chmod +x scripts/*.sh backend/*.sh 2>/dev/null`.
If your Mac's IP differs from `team.env`, tell the team (one person edits `team.env`, runs `./sync.sh`, commits and pushes; everyone else runs `git pull`).

## Phase 1

### Task A
```bash
./scripts/check_lan.sh
```

### Task C — run Backend B
```bash
./backend/run_backend.sh        # creates venv, installs Flask, binds 0.0.0.0:3002. Leave this terminal open.
```
Verify (second terminal here, and **from another Mac**):
```bash
curl -i http://10.7.8.104:3002/api/status           # {"backend":"B",…} + header X-Backend: B
curl -i http://10.7.8.104:3002/api/catalog          # Cache-Control: max-age=60 + ETag (same ETag as Backend A)
lsof -nP -iTCP:3002 -sTCP:LISTEN                 # must show *:3002
```
Click "Allow" on the macOS incoming-connection pop-up for Python.

### Also: be a client
`./scripts/trust_ca.sh` then `./scripts/set_dns.sh primary` (second client for the DNS requirement), then `./scripts/demo_lb.sh`.

### Failure 4 / Ext D
Stop both backends (Mac 3 and Mac 4 Ctrl+C) → 502 at the edge. Stop only B and show A alone serves; restart B and show A/B again.

## Phase 2

### Ext C — Service isolation (pf)
```bash
./scripts/isolate_pf.sh 3002                          # only Mac 2 may reach :3002
# if the standby edge on Mac 3 must also reach it (Ext E):
EXTRA_ALLOW=10.7.1.186 ./scripts/isolate_pf.sh 3002
```
Demonstrate: Mac 2 `curl -i http://10.7.8.104:3002/health` → 200; Mac 1 → timeout; `https://app.team1.test:8443/api/status` still works.
```bash
./scripts/rollback_pf.sh                              # restore + "rollback OK"
```

### Evidence & report help
This Mac's owner typically keeps the **evidence folder** and writes the Phase 2 report: collect screenshots from all Macs into `evidence/` (see `../EVIDENCE_CHECKLIST.md`) and fill the TODOs in `Docs/CN_Project_Master.pdf` chapter 9.

## Be ready to explain (viva)
Why backends use different ports · what `X-Backend` proves · why identical ETags on A and B matter for 304 · what the edge sees when this backend dies (`max_fails`, `fail_timeout`, `proxy_next_upstream`).
