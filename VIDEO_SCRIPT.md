# Submission Video — plan, shot list and narration

Goal: one continuous screen recording (~15–20 min) that follows the official **11-step demo sequence**, with every teammate speaking. Keep it under the size limit your faculty gives (export 1080p, H.264).

## Before recording
1. All four Macs on the same network, IPs final, `git pull` done everywhere, everything running (`./scripts/diagnose.sh` → all PASS on Mac 1).
2. Turn on **Do Not Disturb**, close unrelated apps, increase Terminal font (Cmd +) so text is readable.
3. Have ready: topology diagram + IP table, `evidence/phase1.pcapng` open in Wireshark, browser tab to `https://app.team1.test:8443/api/catalog`.
4. Pre-open terminals (labelled with `echo` or window titles): **Mac 1 client**, **Mac 2 edge**, **Mac 3 backend A**, **Mac 4 backend B**.
5. pf OFF, backends running, `sudo -v` done on Mac 1 (so password prompts don't appear on camera).

## How to record (pick one)
- **Mac 1 screen:** `Cmd+Shift+5` → Record Entire Screen (or QuickTime → File → New Screen Recording), microphone = built-in. Stop from the menu-bar button. Saved to Desktop as `.mov`.
- **Show all Macs:** record each Mac's screen the same way for its own segment (Mac 3/4/2 clips are short), then join clips in QuickTime/iMovie in step order. Or run a Zoom/Meet call, each Mac shares its screen and the call is recorded.
- Voice-over live while doing the steps (evaluators want explanation, not silent clips). Do a dry run first.
- Save as `CN_Project_team1_demo.mp4`; keep the raw clips until submitted.

## Shot list (who speaks / what is shown / command)
| Time | Step | Speaker | On screen | Say (key points) |
|---|---|---|---|---|
| 0:00 | Intro | Mac 1 owner | title slide: team, roles, domain | "private service platform: client → DNS → HTTPS edge → two backends, all local" |
| 1:00 | 1 Topology + inventory | Mac 2 owner | diagram, IP table, service map | each role's cloud equivalent (Route 53, ALB, EC2) |
| 2:30 | 2 LAN | Mac 4 owner | `./scripts/check_lan.sh` on 2 Macs | same subnet → no router, ARP gives MAC |
| 3:30 | Backends | Mac 3 / Mac 4 owners | `./backend/run_backend.sh`, `curl -i http://10.7.1.186:3001/api/status`, `lsof` | binds 0.0.0.0, X-Backend header, fixed ports |
| 5:00 | 3 DNS | Mac 1 owner | `dig app.team1.test`, `cat generated/dnsmasq.conf`, `scutil --dns` | DNS ≠ connection, A record, TTL, UDP/53 |
| 6:30 | 4 HTTPS | Mac 2 owner | `curl -v https://app.team1.test:8443/api/status` + browser padlock/cert viewer | CA, SAN, chain of trust, no `-k`, no IP in URL |
| 8:00 | 5 Load balancing | Mac 2 owner | `./scripts/demo_lb.sh`, show `generated/nginx.conf` upstream + `tail access.log` | round-robin, clients never see backend IPs, L7 |
| 9:30 | 6 Wireshark | Mac 1 owner | `phase1.pcapng` filters `dns`, `tcp.flags.syn==1 && tcp.port==8443`, `tls.handshake`, `tls.record.content_type==23`, Conversations | point to each packet + ports, ISN/ACK, encrypted payload |
| 11:30 | 7 Caching | Mac 4 owner | `./scripts/demo_cache.sh`, browser DevTools cache hit | fresh hit vs conditional (304) vs full 200 |
| 12:30 | 5 Failures | Mac 3 owner | `./scripts/failures.sh 1`…`5` (quick) | which layer each one breaks |
| 14:00 | 8 Backend failure | Mac 3 owner | Ctrl+C Backend A → `demo_lb.sh` all B → restart A | passive health checks (max_fails, fail_timeout) |
| 15:00 | 9 Phase 2 | all | Ext A: `set_dns.sh both`, stop dnsmasq, `dig`; Ext B: `demo_ttl.sh`; Ext E: `demo_edge.sh`; Ext C: `isolate_pf.sh` / blocked from Mac 1 / `rollback_pf.sh` | failover delay, TTL, cutover, least privilege, SPOF = edge |
| 18:00 | 10 Troubleshooting | Mac 1 owner | break something (e.g. stop nginx), run `./scripts/diagnose.sh`, fix | IP → DNS → TCP → TLS → HTTP → backend |
| 19:30 | 11 Wrap-up | each member 20 s | face/voice | one thing each learned; explain any component |

Tips: say the command's purpose before running it · pause 2 s on important output · never type `-k` · never show passwords/private keys (`certs/` is gitignored; don't `cat` keys) · if a command errors, fix it on camera calmly (diagnosing is graded) or cut and retake that segment.

## After recording — assemble the submission
```
submission/
  CN_Project_team1_demo.mp4
  Architecture + report PDF (Docs/CN_Project_Master.pdf with chapter 9 and screenshots filled in)
  evidence/            (screenshots, phase1.pcapng, tls12.pcapng)  – see EVIDENCE_CHECKLIST.md
  config bundle/       (each Mac's generated/dnsmasq.conf, generated/nginx.conf, scripts/)
  backend source/      (_shared/backend/)  or GitHub link: https://github.com/CODERNSINGH/CN-Project-Naren
```
Put the repo link + video in the report. Check the video plays end-to-end with audio before uploading.
