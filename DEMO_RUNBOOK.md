# Final Demo Runbook (11 steps) — run from Mac 1 unless stated

Pre-flight (10 min before): all 4 Macs awake (`caffeinate -d`), same Wi-Fi, backends running, nginx running on Mac 2, dnsmasq on Mac 1 and Mac 3, pf **off**, `phase1.pcapng` ready in Wireshark, browser tab with `https://app.team1.test:8443/api/catalog` open.
Quick health check: `./scripts/diagnose.sh` → everything PASS.

| # | Step | Command / action |
|---|---|---|
| 1 | Topology + inventory | show diagram, IP table (from `check_lan.sh`), service map (README tables) |
| 2 | LAN reachability | `./scripts/check_lan.sh` on two Macs (all `OK`) |
| 3 | Resolve name | `dig app.team1.test` → SERVER = Mac 1, ANSWER = Mac 2 |
| 4 | HTTPS by name | `curl -v https://app.team1.test:8443/api/status` (no `-k`, "SSL certificate verify ok") + browser padlock |
| 5 | Load balancing | `./scripts/demo_lb.sh` → A,B,A,B… |
| 6 | Wireshark | open `evidence/phase1.pcapng`: `dns`, `tcp.flags.syn==1 && tcp.port==8443`, `tls.handshake`, `tls.record.content_type==23` |
| 7 | Caching | `./scripts/demo_cache.sh` (Cache-Control, ETag, 304) + browser cache hit |
| 8 | Fail one backend | Ctrl+C Backend A on Mac 3 → `./scripts/demo_lb.sh` → all `X-Backend: B`; restart A |
| 9 | Phase 2 | pick: Ext A (`set_dns.sh both`; stop dnsmasq on Mac 1; `dig`/`curl` still work) · Ext B (`demo_ttl.sh`) · Ext E (`demo_edge.sh` during cutover) · Ext C (isolate_pf/rollback_pf) |
| 10 | Injected fault | `./scripts/diagnose.sh`, then fix; narrate IP → DNS → TCP → TLS → HTTP → backends |
| 11 | Viva | every member explains any component (see each Mac README "Be ready to explain") |

## Fault cheat-sheet (what faculty may break → how it shows)
| Fault | First FAIL in `diagnose.sh` | Fix |
|---|---|---|
| dnsmasq stopped / wrong client DNS | DNS | `./scripts/set_dns.sh primary`; Mac 1 `sudo brew services restart dnsmasq` |
| DNS record to wrong IP | DNS (record mismatch) | fix `address=` in dnsmasq, restart, flush cache |
| nginx stopped / wrong port | TCP | Mac 2 `nginx` / `./scripts/configure_nginx.sh` |
| cert expired / wrong SAN / CA not trusted | TLS | regenerate certs + reload nginx / `trust_ca.sh` |
| upstream port wrong / backend stopped | HTTP 502 | fix upstream in `generated/nginx.conf` then `configure_nginx.sh`; start backend |
| backend bound to 127.0.0.1 | backends | run with `host="0.0.0.0"` (the provided app does) |
| pf rule blocks edge | backends (direct) fails, edge 502 | `./scripts/rollback_pf.sh` |

Logs: Mac 2 `tail -f "$(brew --prefix)/var/log/nginx/error.log"` · Mac 1 `tail -f /tmp/dnsmasq.log`.
