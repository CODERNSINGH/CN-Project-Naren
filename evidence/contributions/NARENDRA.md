# Narendra: Mac 2, edge, load balancer, TLS and team lead (10.7.7.27)

## What Narendra did
- Built the repository: the four Mac folders, `_shared/` scripts, `team.env`, `setup_team.sh` and `sync.sh`, the runbooks and the Excalidraw diagram with its generator.
- Collected the four IPs and updated `team.env` with `setup_team.sh` when the campus DHCP changed every address.
- Created the team CA and the edge certificate with SAN `app.team1.test` and `api.team1.test` (`make_certs.sh`), and served only the public CA (`serve_ca.sh`). All three teammates downloaded it (p1-04, p1-13).
- Configured nginx on `:8443` (HTTPS, TLS 1.2/1.3) and `:8080` (redirect), with round-robin to Backend A and B, passive health checks (`max_fails=2 fail_timeout=10s`) and retries (`proxy_next_upstream`).
- Fixed the false TLS FAIL in `diagnose.sh`, `demo_tls.sh` and `failures.sh`: LibreSSL's openssl ignores the macOS keychain, so the scripts now pass the CA file with `-CAfile`.
- Wrote the Phase 2 automation (`phase2.sh` per-role runner, `phase2_check.sh`, cert hand-off with `serve_certs.sh`, evidence submit and collect).
- Phase 2: handed the certificate and key to the standby edge on Mac 3 (Ext E), tailed the nginx access log showing the two-upstream retry lines (ED3, Ext D), ran the edge-side pf test (EC3, Ext C) and stopped nginx as the injected fault (EF0, Ext F).
- After the lab, reproduced on Mac 2: the LAN ping matrix (A2), DNS queried from Mac 1 (B8), HTTP caching (F1) and failures 1, 4 and 5 (X1, X4, X5).
- Wrote the final evidence report (`evidence/build_report.py` builds `FINAL_REPORT.md` and `index.html`), including the honest notes for Ext C, D and F.

## Evidence files
`mac2-edge-lb/evidence/` (A2, B8, EC3, ED3, EF0, F1, X1, X4, X5) and `evidence/screenshots/p1-04, 13`.

## Questions Narendra can answer in the viva
How the chain of trust works (CA, signature, SAN), why the certificate survived the DHCP change (it holds names, not IPs), what TLS termination at the edge means, how nginx round-robins and how `max_fails`, `fail_timeout` and `proxy_next_upstream` give failover, what a 502 means, why the single edge is the remaining point of failure and how the standby edge plus a DNS change fixes it.
