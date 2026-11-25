# Keshav: Mac 3, Backend A, backup DNS and standby edge (10.7.29.229)

## What Keshav did
- Ran Backend A on port 3001 (`./backend/run_backend.sh`), later adding request logging, `/api/whoami` and uptime plus request count on `/health`.
- Trusted the CA and set his DNS to the team server (p1-12, p1-18, p1-20).
- Phase 2, Ext A: started the backup DNS on his Mac (`setup_dnsmasq.sh backup`), proven by EA1: dnsmasq listening on 10.7.29.229:53 and answering 10.7.7.27.
- Ext C: turned the pf firewall on for port 3001 so only the edge may connect (EC1), then rolled it back with "rollback OK" (EC5).
- Ext E: received the certificate and key from Mac 2, installed nginx and started the standby edge (EE1: HTTP/2 200, listening on *:8443).
- Ext D: stop and restart of Backend A (ED0 files).

## Evidence files
`mac3-backend-a/evidence/` (EA1, EC1, EC5, ED0 stopped and restarted, EE1) and `evidence/screenshots/p1-02, 08, 12, 18, 20`.

## Questions Keshav can answer in the viva
Why a backend binds to 0.0.0.0 instead of 127.0.0.1, what the pf rules do (pass from the edge, block drop for everyone else), why the standby can reuse the same certificate (it holds names, not IPs), how the backup DNS differs from the primary.
