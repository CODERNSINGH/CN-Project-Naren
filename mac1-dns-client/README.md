# Mac 1 — Private DNS Server + Test Client

**Owner:** Mohan · **IP:** 10.7.16.221 · netmask 255.255.224.0 · gateway 10.7.0.1 (campus Wi-Fi, subnet 10.7.0.0/19) · all IPs: `../team.env`

**Role:** runs **dnsmasq** (answers `app.team1.test` / `api.team1.test` → Mac 2's IP; Route 53 equivalent) and is the main **client** for demos, Wireshark and failure tests.

## Step 0 — Get the code (every teammate, on their own Mac)
```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren      # first time only
cd ~/CN-Project-Naren && git pull               # every time before you start (picks up IP/config changes)
cd mac1-dns-client
```
**Step 0b — find your IP (send it to the team lead):** `./scripts/my_ip.sh` (full explanation + manual commands: `../GUIDE_END_TO_END.md` §3). Then `git pull` once the lead has pushed `team.env`.
Then continue with Phase 1 below. If `./scripts/...` says "permission denied": `chmod +x scripts/*.sh backend/*.sh 2>/dev/null`.
If your Mac's IP differs from `team.env`, tell the team (one person edits `team.env`, runs `./sync.sh`, commits and pushes; everyone else runs `git pull`).

## Phase 1

### Task A — LAN
```bash
./scripts/check_lan.sh
```

### Task B — DNS (do after Mac 3/4 backends are up)
```bash
./scripts/setup_dnsmasq.sh primary       # installs dnsmasq, writes config, starts it with sudo, self-tests
sudo lsof -nP -iUDP:53                   # dnsmasq listening
./scripts/set_dns.sh primary             # this Mac uses itself as resolver
dig app.team1.test                       # SERVER: 10.7.16.221, ANSWER = 10.7.2.91
nslookup app.team1.test
dscacheutil -q host -a name app.team1.test    # system resolver path (what curl/browsers use)
```
Then on **at least one more Mac** (Mac 2/3/4): `./scripts/set_dns.sh primary` and run `dig` there (needed: two clients).
Config saved in `generated/dnsmasq.conf`; query log: `tail -f /tmp/dnsmasq.log`.

### Task E — trust the CA (Mac 2 must be running `serve_ca.sh`)
```bash
./scripts/trust_ca.sh
curl -sI https://app.team1.test:8443/api/status       # no -k, no warnings
```
Browser: open `https://app.team1.test:8443/` → padlock; click it → certificate shows issuer + SAN.

### Task D — load balancing
```bash
./scripts/demo_lb.sh          # six requests → X-Backend A,B,A,B…
```

### Task F — caching
```bash
./scripts/demo_cache.sh       # Cache-Control + ETag, 304 conditional, HTTP versions
```
Browser: DevTools → Network → open `https://app.team1.test:8443/api/catalog`, reload within 60 s → "(memory cache)". Cmd+Shift+R → full 200.

### Task E proof — TLS
```bash
./scripts/demo_tls.sh         # TLS version, cipher, "Verify return code: 0 (ok)", TLS 1.2 forced
```

### Task G — Wireshark evidence (GUI, interface en0)
1. Start Wireshark on `en0` (capture filter `host 10.7.16.221 or host 10.7.2.91`).
2. In Terminal:
   ```bash
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder     # force a real DNS query
   curl -v https://app.team1.test:8443/api/status
   for i in 1 2 3 4; do curl -sI https://app.team1.test:8443/api/status | grep -i x-backend; done
   curl -v --tlsv1.2 --tls-max 1.2 https://app.team1.test:8443/      # shows the Certificate packet
   ```
3. Stop, save **`evidence/phase1.pcapng`**. Filters: `dns` · `tcp.flags.syn==1 && tcp.port==8443` · `tls.handshake` · `tls.record.content_type==23` · Statistics→Conversations.
   (CLI alternative: `./scripts/capture.sh phase1` → `evidence/phase1.pcap`.)
   Optional decrypt: `export SSLKEYLOGFILE=$HOME/tlskeys.log` with Chrome/Homebrew curl, load the file in Wireshark → Protocols → TLS.

### Five required failure demos
```bash
./scripts/failures.sh 1      # wrong DNS server (auto-breaks and restores)
# 2: on Mac 1:  APP_IP=10.7.8.104 ./scripts/setup_dnsmasq.sh primary   then   ./scripts/failures.sh 2
#    restore:   ./scripts/setup_dnsmasq.sh primary   (+ flush client cache)
# 3: Ctrl+C Backend A on Mac 3, then  ./scripts/failures.sh 3
# 4: stop both backends, then          ./scripts/failures.sh 4     (502, DNS+TLS fine)
./scripts/failures.sh 5      # wrong port 9999
```
Screenshot each and write one sentence of "why" (see `Docs/CN_Project_Master.pdf` ch. 4).

## Phase 2
- **Ext A backup DNS** (Mac 3 runs `setup_dnsmasq.sh backup`):
  ```bash
  ./scripts/set_dns.sh both                       # primary Mac 1, then backup
  sudo brew services stop dnsmasq                 # kill primary
  dig +short app.team1.test @10.7.1.186        # backup answers
  dig +tries=1 +time=2 app.team1.test @10.7.16.221    # primary: no response
  curl -sI https://app.team1.test:8443/ | head -1 # works after a short fallback delay
  sudo brew services start dnsmasq                # restore
  ```
- **Ext B TTL** (change **both** DNS servers, or stop the backup first):
  ```bash
  TTL=30 ./scripts/setup_dnsmasq.sh primary       # 30 s TTL
  # terminal A (client):  ./scripts/demo_ttl.sh
  APP_IP=10.7.8.104 TTL=30 ./scripts/setup_dnsmasq.sh primary    # change record → old answer persists ≤30 s
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder   # immediate change
  ./scripts/setup_dnsmasq.sh primary              # restore original record/TTL
  ```
- **Ext E cutover:** `TTL=30 APP_IP=10.7.1.186 ./scripts/setup_dnsmasq.sh primary` (and on backup), watch `./scripts/demo_edge.sh` → `edge=mac2` flips to `edge=standby`.
- **Ext F:** `./scripts/diagnose.sh` — read the first FAIL (IP→DNS→TCP→TLS→HTTP→backends).

## Be ready to explain (viva)
DNS vs the TCP/HTTPS connection that follows · A record + TTL · why UDP/53 · `dig` vs system resolver cache · `.test` vs `.local` · DNS failure vs app failure · resolver failover is sequential with timeout · TTL and migration · all Wireshark packets and ports (53/UDP, ephemeral→8443/TCP).
