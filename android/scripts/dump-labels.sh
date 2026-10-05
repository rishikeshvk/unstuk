#!/usr/bin/env bash
# Dumps the labels on the Quick Settings pages and the Settings screens the executor visits, for the node-label
# test set (M3 step 10), into data/nodes/<device>/<screen>.json.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/dump-labels.sh [device name, default: moto]
#   Needs a debug build installed, the phone unlocked, and Unstuk's accessibility service allowed.
set -euo pipefail

source "$(dirname "$0")/device.sh"
RECEIVER=$PKG/.debug.LabelDumpReceiver
SCREENS=(qs network bluetooth sound dnd display accessibility date_time)

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
repo_root=$(cd "$(dirname "$0")/../.." && pwd)
out_dir="$repo_root/data/nodes/${1:-moto}"
mkdir -p "$out_dir"

ensure_ready
for screen in "${SCREENS[@]}"; do
    sh_adb "run-as $PKG rm -f files/labels/$screen.json"
    # In the background: am broadcast blocks until the receiver finishes (M2 lesson).
    sh_adb am broadcast -n "$RECEIVER" -a "$PKG.debug.DUMP_LABELS" --es screen "$screen" >/dev/null &
    for _ in $(seq 1 "$RESULT_TIMEOUT_S"); do
        sh_adb "run-as $PKG ls files/labels/$screen.json" >/dev/null 2>&1 && break
        sleep 1
    done
    wait
    if ! sh_adb "run-as $PKG cat files/labels/$screen.json" >"$out_dir/$screen.json" 2>/dev/null; then
        echo "$screen: no dump within ${RESULT_TIMEOUT_S}s" >&2
        rm -f "$out_dir/$screen.json"
        continue
    fi
    echo "$screen: $(grep -o '"page"' "$out_dir/$screen.json" | wc -l | tr -d ' ') nodes"
done
