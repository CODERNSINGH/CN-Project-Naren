# Mohan: Mac 1, DNS server and test client (10.7.9.43)

## What Mohan did
- Turned off Cloudflare WARP so the team DNS was not ignored (screenshots p1-01, p1-05).
- Set up the private DNS server: `./scripts/setup_dnsmasq.sh primary` (p1-09). dnsmasq answers `app.team1.test` with the edge IP `10.7.7.27`.
- Trusted the team CA and pointed his resolver at his own DNS (p1-10).
- Ran the Phase 1 checks: `diagnose.sh` (found a false TLS FAIL, then all PASS, p1-14 and p1-15), `demo_lb.sh` (A,B alternate, p1-16), `demo_tls.sh` (TLS 1.3, verify code 0, p1-17).
- Phase 2: backup DNS failover (EA2, page loaded in 2.55 s with the primary stopped), TTL timeline (EB), DNS cutover to the standby edge (EE2), diagnose runs and final readiness check (EF1 to EF3).

## Evidence files
`mac1-dns-client/evidence/` (EA0, EA2, EB, EC4, ED1, ED2, EE0, EE2, EF1, EF2, EF3) and `evidence/screenshots/p1-01, 05, 06, 09, 10, 14, 15, 16, 17, 21`.

## Questions Mohan can answer in the viva
DNS versus the TCP/TLS connection that follows it, what a TTL is and what the timeline showed, why resolver failover costs one timeout, why the first diagnose TLS check was a false FAIL (openssl does not read the macOS keychain).
