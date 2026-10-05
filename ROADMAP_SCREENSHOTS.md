# ROADMAP — what to run, in order, and what to screenshot

You run every command yourselves. Each row = **who · where · command · what you must see · screenshot name**.
Save screenshots in `evidence/` with the names shown (Cmd+Shift+4 on Mac; include the terminal prompt + command in the shot).
IPs: Mohan Mac 1 `10.7.16.221` · Narendra Mac 2 `10.7.2.91` · Keshav Mac 3 `10.7.1.186` · Mayank Mac 4 `10.7.8.104` · router `10.7.0.1` · domain `app.team1.test:8443`.

## 0. Before anything (everyone)
```bash
git clone https://github.com/CODERNSINGH/CN-Project-Naren.git ~/CN-Project-Naren   # or: cd ~/CN-Project-Naren && git pull
cd ~/CN-Project-Naren/<your folder>     # mac1-dns-client | mac2-edge-lb | mac3-backend-a | mac4-backend-b
```
Mohan: turn **OFF** Cloudflare WARP / VPN / DNS filter app (his DNS showed `127.0.2.2`).
Narendra (Mac 2): this laptop already has a build from earlier. To redo it cleanly with screenshots run **once**: `cd "/Users/Narendra/Desktop/NST/CN Project/mac2-edge-lb" && git pull && ./scripts/reset_mac2.sh` (type YES). Skip if you don't care.

## PHASE 1

### Task A — LAN (all four Macs, any order)
| # | Who | Command | You must see | Screenshot |
|---|---|---|---|---|
| A1 | each | `./scripts/my_ip.sh` | your IP, mask 255.255.224.0, gateway 10.7.0.1, MAC addr, router ping OK | `A1-ip-info-mac1.png` … `mac4.png` |
| A2 | each | `./scripts/check_lan.sh` | OK for all 4 Macs | `A2-ping-matrix-macN.png` |
| A3 | any | draw the topology (use the `.excalidraw` file, section 1) | 4 roles + IPs | `A3-topology.png` |

### Task C — Backends (start these FIRST)
| # | Who | Command | You must see | Screenshot |
|---|---|---|---|---|
| C1 | Keshav | `./backend/run_backend.sh` (leave open) | `Running on http://0.0.0.0:3001` | `C1-backendA-running.png` |
| C2 | Mayank | `./backend/run_backend.sh` (leave open) | `Running on http://0.0.0.0:3002` | `C2-backendB-running.png` |
| C3 | Keshav | `lsof -nP -iTCP:3001 -sTCP:LISTEN` | `*:3001` | `C3-lsof-3001.png` |
| C4 | Mayank | `lsof -nP -iTCP:3002 -sTCP:LISTEN` | `*:3002` | `C4-lsof-3002.png` |
| C5 | **Mohan** (another Mac!) | `curl -i http://10.7.1.186:3001/api/status` | `{"backend":"A"…}` + `X-Backend: A` | `C5-curl-A-from-mac1.png` |
| C6 | **Mohan** | `curl -i http://10.7.8.104:3002/api/status` | `X-Backend: B` | `C6-curl-B-from-mac1.png` |

### Task B — DNS (Mohan, Mac 1)
| # | Command | You must see | Screenshot |
|---|---|---|---|
| B1 | `./scripts/setup_dnsmasq.sh primary` | password prompt, `dnsmasq: syntax check OK`, dig answer `10.7.2.91` | `B1-dnsmasq-setup.png` |
| B2 | `sudo lsof -nP -iUDP:53` | dnsmasq on `10.7.16.221:53` | `B2-dnsmasq-listening.png` |
| B3 | `cat generated/dnsmasq.conf` | the records | `B3-dnsmasq-conf.png` |
| B4 | `./scripts/set_dns.sh primary` | `nameserver … 10.7.16.221`, **no red WARNING** | `B4-set-dns-mac1.png` |
| B5 | `dig app.team1.test` · `nslookup app.team1.test` | `SERVER: 10.7.16.221`, ANSWER `10.7.2.91` | `B5-dig-mac1.png`, `B5-nslookup-mac1.png` |
| B6 | `dscacheutil -q host -a name app.team1.test` · `scutil --dns \| head -30` | ip_address 10.7.2.91 | `B6-system-resolver.png` |
| B7 | **second client** (Keshav or Mayank): `./scripts/set_dns.sh primary` then `dig app.team1.test` | same answer | `B7-dig-second-client.png` |

### Task E — Edge + TLS (Narendra, Mac 2)
| # | Command | You must see | Screenshot |
|---|---|---|---|
| E1 | `brew install nginx` *(skip if present; `nginx -V` fine)* | installed | `E1-nginx-installed.png` |
| E2 | `./scripts/make_certs.sh` | `app.crt: OK`, SAN lines | `E2-make-certs.png` |
| E3 | `openssl x509 -in certs/app.crt -noout -text \| grep -A1 "Subject Alternative"` | DNS:app.team1.test, DNS:api.team1.test | `E3-cert-san.png` |
| E4 | `./scripts/configure_nginx.sh` | `nginx -t … successful`, `*:8443 LISTEN` | `E4-nginx-up.png` |
| E5 | `cat generated/nginx.conf` | upstream with both backends | `E5-nginx-conf.png` |
| E6 | `./scripts/serve_ca.sh` (leave running) | serving `http://10.7.2.91:8000/ca.crt` | `E6-serve-ca.png` |
| E7 | Mohan, Keshav, Mayank each: `./scripts/trust_ca.sh` (password) | `CA trusted`, fingerprint **identical** on all | `E7-trust-ca-macN.png` |
| E8 | then Narendra: Ctrl+C `serve_ca.sh` | | |

### Task D — Load balancing (Mohan)
| # | Command | You must see | Screenshot |
|---|---|---|---|
| D1 | `./scripts/demo_lb.sh` | `X-Backend: A, B, A, B, A, B` — **PHASE 1 GATE** | `D1-lb-loop.png` |
| D2 | Narendra: `tail -n 12 /opt/homebrew/var/log/nginx/access.log` | `xb=A` / `xb=B` alternating | `D2-nginx-access-log.png` |
| D3 | browser: `https://app.team1.test:8443/` | padlock, no warning, JSON | `D3-browser.png` |

### Task E proof (Mohan)
| # | Command | You must see | Screenshot |
|---|---|---|---|
| T1 | `./scripts/demo_tls.sh` | `SSL certificate verify ok`, TLS 1.3, `Verify return code: 0 (ok)` | `E-tls-proof.png` |
| T2 | browser: click padlock → certificate | issuer `team1 Local CA`, SAN | `E-browser-cert.png` |

### Task F — Caching (Mohan)
| # | Command | You must see | Screenshot |
|---|---|---|---|
| F1 | `./scripts/demo_cache.sh` | `Cache-Control: max-age=60`, `ETag`, then `304 NOT MODIFIED` | `F1-headers.png`, `F2-304.png` |
| F2 | Chrome → DevTools → Network → open `/api/catalog`, reload within 60 s | `(memory cache)` / `disk cache` | `F3-devtools-cache.png` |

### Task G — Wireshark (Mohan; Wireshark: `brew install --cask wireshark`)
1. Wireshark → interface `en0` → capture filter `host 10.7.16.221 or host 10.7.2.91` → Start.
2. Terminal: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` then `curl -v https://app.team1.test:8443/api/status` then `for i in 1 2 3 4; do curl -sI https://app.team1.test:8443/api/status | grep -i x-backend; done` then `curl -v --tlsv1.2 --tls-max 1.2 https://app.team1.test:8443/`.
3. Stop, **save `evidence/phase1.pcapng`**.

| # | Display filter | Screenshot (point at the packets) |
|---|---|---|
| G1 | `dns` | `G1-dns.png` (query UDP→53 + answer 10.7.2.91) |
| G2 | `tcp.flags.syn==1 && tcp.port==8443` | `G2-tcp-handshake.png` (SYN, SYN-ACK; then ACK) |
| G3 | `tls.handshake` | `G3-tls-handshake.png` (ClientHello SNI, ServerHello, Certificate in the TLS 1.2 capture) |
| G4 | `tls.record.content_type==23` | `G4-encrypted-data.png` |
| G5 | Statistics → Conversations | `G5-conversations.png` (ports 53/UDP, 8443/TCP) |

### The 5 failure demos (Mohan; screenshot each)
| # | Command | You must see | Screenshot |
|---|---|---|---|
| X1 | `./scripts/failures.sh 1` | dig timeout, ping works, restore | `X1-wrong-dns.png` |
| X2 | Mac 1: `APP_IP=10.7.8.104 ./scripts/setup_dnsmasq.sh primary`, then `./scripts/failures.sh 2`; restore with `./scripts/setup_dnsmasq.sh primary` | dig OK but wrong host | `X2-wrong-record.png` |
| X3 | Keshav Ctrl+C backend A, Mohan `./scripts/failures.sh 3`; restart A | all `X-Backend: B` | `X3-one-backend.png` |
| X4 | stop both backends, `./scripts/failures.sh 4`; restart both | `502 Bad Gateway`, TLS ok | `X4-both-down.png` |
| X5 | `./scripts/failures.sh 5` | refused / SYN→RST in Wireshark | `X5-wrong-port.png` |

## PHASE 2
| # | Ext | Who | Command | You must see | Screenshot |
|---|---|---|---|---|---|
| P1 | A | Keshav | `./scripts/setup_dnsmasq.sh backup` | `dig +short app.team1.test @10.7.1.186` → 10.7.2.91 | `EA1-backup-dns.png` |
| P2 | A | Mohan | `./scripts/set_dns.sh both` → `sudo brew services stop dnsmasq` → `dig +tries=1 +time=2 app.team1.test @10.7.16.221` (fails) → `curl -sI https://app.team1.test:8443/ \| head -1` (works) → `sudo brew services start dnsmasq` | primary dead, backup serves | `EA2-failover.png` |
| P3 | B | Mohan | `TTL=30 ./scripts/setup_dnsmasq.sh primary` (Keshav the same with `backup`); terminal 1 `./scripts/demo_ttl.sh`; terminal 2 `APP_IP=10.7.8.104 TTL=30 ./scripts/setup_dnsmasq.sh primary`; later flush `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`; restore `./scripts/setup_dnsmasq.sh primary` | old IP persists ≤30 s, then new; flush = instant | `EB-ttl-timeline.png` |
| P4 | C | Keshav | `./scripts/isolate_pf.sh 3001` | rules shown | `EC1-pf-on-mac3.png` |
| P5 | C | Mayank | `./scripts/isolate_pf.sh 3002` | rules shown | `EC2-pf-on-mac4.png` |
| P6 | C | Narendra | `curl -i http://10.7.1.186:3001/health` | **200** | `EC3-edge-allowed.png` |
| P7 | C | Mohan | `curl -m 5 -i http://10.7.1.186:3001/health` · `nc -vz -w 3 10.7.1.186 3001` · `curl -s https://app.team1.test:8443/api/status` | timeout, fail, **still works via edge** | `EC4-client-blocked.png` |
| P8 | C | Keshav, Mayank | `./scripts/rollback_pf.sh` | `rollback OK` | `EC5-rollback-ok.png` |
| P9 | D | Keshav + Mohan | stop backend A → `./scripts/demo_lb.sh` (all B) → start A → wait 15 s → `demo_lb.sh` (A/B) | failover + recovery | `ED1-failover.png`, `ED2-recovery.png` |
| P10 | E | Narendra → Keshav | copy `certs/app.crt app.key` to Keshav (`scp certs/app.* keshav@10.7.1.186:~/CN-Project-Naren/mac3-backend-a/certs/` after `mkdir -p` there, or AirDrop); Keshav `brew install nginx && ./scripts/configure_nginx.sh standby` | standby on 8443 | `EE1-standby.png` |
| P11 | E | Mohan | `TTL=30 ./scripts/setup_dnsmasq.sh primary` ; terminal 1 `./scripts/demo_edge.sh`; terminal 2 `APP_IP=10.7.1.186 TTL=30 ./scripts/setup_dnsmasq.sh primary` | `edge=mac2` → `edge=standby` | `EE2-cutover.png` |
| P12 | F | Mohan | `./scripts/diagnose.sh` (healthy, all PASS) then ask a teammate to break one thing, run again | first FAIL names the layer | `EF1-diagnose-ok.png`, `EF2-diagnose-fault.png` |

## FINAL
1. Rehearse with `DEMO_RUNBOOK.md` (11 steps). 2. Record with `VIDEO_SCRIPT.md`. 3. Fill report chapter 9 (`Docs/CN_Project_Master.pdf`) with the screenshots/timestamps. 4. `git add evidence && git commit && git push`.

## If something fails (one line each)
- Any problem → on Mohan `./scripts/diagnose.sh`, fix the **first FAIL**.
- Script says "does not have IP …" → your DHCP IP changed → tell Narendra (`README.md` §6).
- Red WARNING about 127.x → turn off WARP/VPN.
- 502 → a backend isn't running. · cert error / exit 60 → run `./scripts/trust_ca.sh`.
- DNS broken after the project → `./scripts/set_dns.sh restore`.
