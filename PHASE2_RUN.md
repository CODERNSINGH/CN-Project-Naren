# PHASE 2 — run sheet (everything is automated; you only press Enter at sync points)

## 0. Before tonight (everyone, 5 min)
```bash
cd ~/CN-Project-Naren && git pull
cd <your folder>        # mac1-dns-client | mac2-edge-lb | mac3-backend-a | mac4-backend-b
./scripts/my_ip.sh      # must equal team.env — if not, STOP and tell Narendra (README §6)
```
- Wi-Fi same for all, VPN/WARP **off**, `caffeinate -d` in a spare terminal.
- **Screenshots are automatic** (`screencapture`). Allow it once: *System Settings → Privacy & Security → Screen Recording → turn on Terminal* → quit and reopen Terminal. If it still fails the script tells you to press Cmd+Shift+3 and name the file.
- Phase 1 must be working: backends running (Keshav, Mayank), nginx up (Narendra), dnsmasq up (Mohan), everybody `trust_ca.sh` + `set_dns.sh primary` done.
- Keep **one terminal** per person for `phase2.sh` and (Keshav, Mayank) another for the backend.

## 1. The ONLY commands each teammate runs
```bash
cd ~/CN-Project-Naren && git pull && cd <your folder>
./scripts/phase2.sh
```
…and at the very end: `./scripts/submit_evidence.sh` (pushes their PNG/TXT to GitHub).
Re-do one stage: `./scripts/phase2.sh 4`. Pre-flight only: `./scripts/phase2.sh 0`.

### Paste this in the group chat
> Phase 2 tonight. Everyone: `cd ~/CN-Project-Naren && git pull`, go into your Mac folder, run **`./scripts/phase2.sh`**. Yellow `>>>` lines = wait for the teammate named there. When a line says "TELL THE TEAM: …" type that sentence in the chat. At the end run **`./scripts/submit_evidence.sh`**. Don't skip stages; screenshots are automatic. Mohan keeps his terminal visible during timelines.

## 2. Order of play (who says what) — Narendra, this is your conductor sheet
| Stage | Keshav (Mac 3) | Mohan (Mac 1) | Mayank (Mac 4) | Narendra (Mac 2) |
|---|---|---|---|---|
| **0** pre-flight | `phase2.sh 0` passes | passes | passes | passes (nginx + certs) |
| **1 Ext A** backup DNS | starts backup dnsmasq → says **"backup DNS is up"** | waits → `set_dns.sh both`, stops dnsmasq, dig + curl still work → says **"stage 1 done"** | – | – |
| **2 Ext D** failover | stops Backend A → **"A is stopped"** … restarts → **"A is back"** | `demo_lb` all B, waits 15 s, `demo_lb` A/B → **"recovery run done"** | – | access-log screenshot (after "recovery run done") |
| **3 Ext B** TTL | sets TTL=30 on backup → **"TTL set on backup"** | records timeline: record change +15 s, flush +55 s → **"TTL experiment done"** | – | – |
| **4 Ext C** pf | pf on :3001 → **"pf is on (Mac 3)"** | after Keshav+Mayank+Narendra: blocked test → **"rollback pf now"** | pf on :3002 → **"pf on Mac 4"** | after both pf on: allowed test (200) → **"edge test done"** |
| **5 Ext E** standby + cutover | gets certs, starts standby nginx → **"standby up"** | cutover timeline `edge=mac2 → standby`, then restores DNS → **"cutover done"** | – | runs `phase2.sh` stage 5 first: serves certs to Keshav (only his IP, stops itself) |
| **6 Ext F** troubleshoot | – | diagnose OK → **"EF1 captured"** | – | stops nginx → **"fault injected"** → Mohan diagnoses → Narendra restarts → **"fixed"** |

Important ordering tips: in stage 5, Narendra starts **first** (cert serving) and says so; Keshav then continues. Stage 4 rollback happens **before** stage 5 so the standby can reach both backends.

## 3. What you (Narendra) do, step by step
1. `./scripts/phase2.sh 0` — fix anything red.
2. Stage 1, 3: nothing; just watch (you may answer questions).
3. Stage 2: wait for Mohan's **"recovery run done"** → script saves `ED3-access-log` (shows `xb=B,B,B… then A,B`).
4. Stage 4: wait for **both** pf messages → script curls A and B from the edge (200) → tell Mohan **"edge test done"**.
5. Stage 5: press Enter → certs are served to Keshav → tell him. Nothing else.
6. Stage 6: when Mohan says "EF1 captured", press Enter (nginx stops) → tell him; after "EF2 captured" press Enter (nginx restarts) → tell him **"fixed"**.
7. `./scripts/submit_evidence.sh`, then at repo root `./collect_evidence.sh` — it pulls everyone's files into `evidence/` and prints **OK/MISSING** per screenshot.
8. Fill `PHASE2_REPORT.md` (and chapter 9 of the PDF) with the screenshots and the timeline numbers.

## 4. DNS part in plain words (what actually happens)
- Primary DNS = Mac 1 (`10.7.16.221`), backup = Mac 3 (`10.7.1.186`), both answer `app.team1.test → 10.7.2.91`.
- Client list is Mac 1 then Mac 3 (`set_dns.sh both`). Stop Mac 1's dnsmasq → first query times out → macOS asks Mac 3 → site still opens (slightly slower).
- TTL: `TTL=30` makes each answer cacheable for 30 s. Change the record → clients keep the old IP ≤ 30 s; flush = instant.
- Cutover: DNS record changed to `10.7.1.186` (standby nginx) → `X-Edge` flips `mac2 → standby` after TTL. Mohan restores the record to Mac 2 right after.
- Cleanup when the whole project is finished (not tonight): every Mac `./scripts/set_dns.sh restore`.

## 5. Evidence produced (names the report expects)
`EA1-backup-dns EA2-failover EB-ttl-timeline EC1-pf-on-mac3 EC2-pf-on-mac4 EC3-edge-allowed EC4-client-blocked EC5-rollback-ok-mac3 EC5-rollback-ok-mac4 ED1-failover ED2-recovery ED3-access-log EE1-standby EE2-cutover EF1-diagnose-ok EF2-diagnose-fault` (each `.png` + `.txt`, extras `EA0/ED0/EE0/EF0/EF3`).

## 6. If something goes wrong
| Problem | Fix |
|---|---|
| "IP mismatch" / script refuses | DHCP changed an IP → `my_ip.sh`, Narendra `./setup_team.sh …`, push, everyone `git pull`, re-run `setup_dnsmasq.sh` / `configure_nginx.sh` |
| Blank/failed screenshot | enable Screen Recording for Terminal; or Cmd+Shift+3 and save as `evidence/<NAME>.png`; the `.txt` is already saved |
| pf left on | `./scripts/rollback_pf.sh` |
| 502 after stage 4/5 | pf still on or a backend stopped → `./scripts/diagnose.sh`, read the first FAIL |
| DNS weird after stage 3/5 | `./scripts/setup_dnsmasq.sh primary` (and `backup` on Mac 3), `sudo dscacheutil -flushcache` |
| Script stuck on a yellow `>>>` | it is waiting for the teammate named in the line — ask them |
