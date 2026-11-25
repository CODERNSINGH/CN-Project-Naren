# Mayank: Mac 4, Backend B (10.7.25.176)

## What Mayank did
- Checked his IP and router reachability with `my_ip.sh` (p1-03), and again after the fresh clone (p1-07). A brief Wi-Fi drop showed `No route to host` once; re-joining the Wi-Fi fixed it.
- Ran Backend B on port 3002 (`./backend/run_backend.sh`). From Mohan's Mac it answered directly with HTTP 200 and `X-Backend: B`, which is the B half of the A,B,A,B load-balancing result.
- Acted as a client: trusted the team CA (same fingerprint as everyone else) and pointed his DNS at Mac 1 (p1-11, p1-19, p1-22). His old manual DNS (1.1.1.1) was saved first so it can be restored with `set_dns.sh restore`.
- Phase 2, Ext C: turned the pf firewall on for port 3002 so only the edge (10.7.7.27) may connect (EC2: `pass in quick ... from 10.7.7.27 to any port = 3002` then `block drop in quick ... port = 3002`), then rolled it back with "rollback OK (rules identical to before)" (EC5).
- Added the team member details to the README.

## Evidence files
`mac4-backend-b/evidence/` (EC2, EC5) and `evidence/screenshots/p1-03, 07, 11, 19, 22`.

## Questions Mayank can answer in the viva
Why Backend B uses a different port from A (3002 vs 3001), why it binds to 0.0.0.0 and not 127.0.0.1, what the `X-Backend` header proves, what the two pf rules do and why `block drop` gives a timeout instead of "connection refused", why the rollback copy matters, and what happens to the site when Backend B is down (nginx sends everything to A).
