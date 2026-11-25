#!/usr/bin/env bash
# Narendra (repo root): pull everyone's evidence into ./evidence and list what is still missing.
cd "$(dirname "$0")"
git pull --rebase -q
mkdir -p evidence
for d in mac1-dns-client mac2-edge-lb mac3-backend-a mac4-backend-b; do
  [ -d "$d/evidence" ] && cp -n "$d"/evidence/* evidence/ 2>/dev/null
done
EXPECT="EA1-backup-dns EA2-failover EB-ttl-timeline EC1-pf-on-mac3 EC2-pf-on-mac4 EC3-edge-allowed EC4-client-blocked EC5-rollback-ok-mac3 EC5-rollback-ok-mac4 ED1-failover ED2-recovery ED3-access-log EE1-standby EE2-cutover EF1-diagnose-ok EF2-diagnose-fault"
miss=0
for n in $EXPECT; do
  if [ -s "evidence/$n.png" ]; then echo "  OK       $n.png"; else echo "  MISSING  $n.png  (txt: $( [ -s evidence/$n.txt ] && echo yes || echo no ))"; miss=1; fi
done
echo; [ $miss = 0 ] && echo "All Phase 2 screenshots present." || echo "Missing items above: ask the owner to re-run that stage: ./scripts/phase2.sh <stage>"
