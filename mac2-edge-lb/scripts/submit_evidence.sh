#!/usr/bin/env bash
# One command to send YOUR screenshots/logs to GitHub:   ./scripts/submit_evidence.sh
source "$(dirname "$0")/lib.sh"
REPO="$(cd "$ROOT_DIR/.." && pwd)"
ls "$EVID" | grep -q . || { c_bad "evidence/ is empty - run ./scripts/phase2.sh first"; exit 1; }
git -C "$REPO" add -f "$EVID"
if git -C "$REPO" diff --cached --quiet; then c_info "nothing new to commit"; else
  git -C "$REPO" commit -q -m "Phase 2 evidence from $(basename "$ROOT_DIR")"; fi
git -C "$REPO" pull --rebase -q && git -C "$REPO" push -q && c_ok "evidence pushed. Tell Narendra to run ./collect_evidence.sh"
