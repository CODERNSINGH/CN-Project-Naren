# Evidence Checklist (put everything in `evidence/`, name files as below — "30-second rule")

## Phase 1
| File | Task | How |
|---|---|---|
| `A1-ip-info-mac{1..4}.png` | A | `./scripts/check_lan.sh` on each Mac |
| `A2-ping-matrix.png` | A | ping output between all pairs |
| `A3-topology.png` | A | draw the diagram (4 roles, IPs) |
| `B1-dig-client1.png`, `B2-dig-client2.png`, `B3-scutil-dns.png` | B | `dig app.team1.test`, `scutil --dns` on two Macs |
| `B4-dnsmasq.conf` | B | `mac1-dns-client/generated/dnsmasq.conf` |
| `C1-backend-A.png`, `C2-backend-B.png`, `C3-lsof.png` | C | `curl -i` from another Mac, `lsof -nP -iTCP:3001 -sTCP:LISTEN` |
| `D1-lb-loop.png`, `D2-nginx.conf` | D | `./scripts/demo_lb.sh`, `mac2-edge-lb/generated/nginx.conf` |
| `E1-curl-v.png`, `E2-cert-text.png`, `E3-browser-padlock.png`, `E4-s_client.png` | E | `./scripts/demo_tls.sh`, `openssl x509 -text` |
| `F1-headers.png`, `F2-304.png`, `F3-devtools-cache.png` | F | `./scripts/demo_cache.sh`, DevTools |
| `phase1.pcapng`, `tls12.pcapng`, `G1..G4-*.png` | G | Wireshark filters `dns`, `tcp.flags.syn==1`, `tls.handshake`, `tls.record.content_type==23` |
| `X1..X5-failure-N.png` | failures | `./scripts/failures.sh 1..5` |

## Phase 2
| File | Ext | How |
|---|---|---|
| `EA-backup-dns.png` | A | primary stopped, `dig @backup`, `curl` works |
| `EB-ttl-timeline.png` | B | `./scripts/demo_ttl.sh` output with timestamps (old → new → after flush) |
| `EC-pf-allowed.png`, `EC-pf-blocked.png`, `EC-via-edge.png`, `EC-rollback-ok.png` | C | Mac 2 vs Mac 1 curl; rollback output |
| `ED-failover.png` | D | A stopped → all B; A restarted → A/B |
| `EE-x-edge-timeline.png` | E | `./scripts/demo_edge.sh` during cutover |
| `EF-diagnose.png` + notes | F | `./scripts/diagnose.sh` + what you fixed |

Also keep: `Docs/CN_Project_Master.pdf` chapter 9 TODOs filled (test log + timestamps), each Mac's `generated/` configs, and the `_shared/backend/` code (zip or GitHub).
Tip: macOS screenshot = Cmd+Shift+4; terminal text: copy into the PNG or save with `script`/`tee`, e.g. `./scripts/demo_lb.sh | tee evidence/D1-lb-loop.txt`.
