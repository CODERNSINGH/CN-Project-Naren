#!/usr/bin/env bash
# Task G: command-line capture (open the .pcap in Wireshark afterwards, or just use Wireshark's GUI).
#   Terminal 1:  ./capture.sh phase1
#   Terminal 2:  flush DNS, then run requests (see README).  Ctrl+C terminal 1 to stop.
source "$(dirname "$0")/lib.sh"
NAME="${1:-phase1}"
IFACE="$(default_iface)"
mkdir -p "$ROOT_DIR/evidence"
OUT="$ROOT_DIR/evidence/$NAME.pcap"
c_info "Capturing on $IFACE -> $OUT  (DNS from Mac 1 + HTTPS to Mac 2). Ctrl+C to stop."
sudo tcpdump -i "$IFACE" -w "$OUT" "host $MAC1_IP or host $MAC2_IP"
