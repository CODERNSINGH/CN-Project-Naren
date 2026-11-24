# Phase 2 report (fill during the demo) — paste into chapter 9 of the master PDF

Team: team1 · Date: ____ · Readiness check: `./scripts/phase2_check.sh` (Mac 1) → paste output: ____

| Ext | What we did | Commands | Observed (timestamps) | Evidence file | Why it works |
|---|---|---|---|---|---|
| A Backup DNS | second dnsmasq on Mac 3; client lists both | `setup_dnsmasq.sh backup`, `set_dns.sh both`, stop primary, `dig`, `curl` | | EA1/EA2 | resolver tries servers in order, timeout then next |
| B TTL | TTL=30 on both servers, change record | `TTL=30 setup_dnsmasq.sh primary`, `demo_ttl.sh`, flush | old IP persisted ___ s | EB | cache honours TTL until expiry; flush forces re-query |
| C Isolation | pf: only Mac 2 may reach 3001/3002 | `isolate_pf.sh`, curl from Mac 2 vs Mac 1, `rollback_pf.sh` | | EC1–EC5 | L3/L4 filter, drop = timeout, least privilege |
| D HA failover | stop backend A, then restart | `demo_lb.sh` | all B → A/B after ___ s | ED1/ED2 | passive health check max_fails=2, fail_timeout=10s, proxy_next_upstream |
| E Edge migration | standby nginx on Mac 3, DNS cutover | `configure_nginx.sh standby`, `demo_edge.sh` | edge=mac2 → standby at ___ | EE1/EE2 | same cert (names), DNS record change, TTL bounds cutover time |
| F Troubleshooting | injected fault found by layer | `diagnose.sh` | first FAIL: ___ fixed by: ___ | EF1/EF2 | IP → DNS → TCP → TLS → HTTP → backends |

SPOF discussion: single edge is the SPOF; mitigated by standby edge + DNS cutover (manual, TTL-bound). Further: keepalived/VRRP, cloud LB.
Cloud mapping: dnsmasq=Route 53, nginx=ALB, pf=security groups, backends=EC2.
