#!/usr/bin/env bash
# Runs executor trials of catalog fixes on one device over adb, cross-checks every result with an independent
# state read, and prints success counts, 95% Wilson intervals and median times per fix.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/trials.sh [trials-per-fix] [fix id ...]
#   fixes: any fix with an automated rung that device.sh can break (default: airplane_off dnd_off).
#   Needs a debug build installed.
set -euo pipefail

source "$(dirname "$0")/device.sh"
RECEIVER=$PKG/.debug.TrialReceiver
CONDITIONS=(home other_app shade_open)

trials=${1:-20}
shift || true
fixes=("$@")
[ ${#fixes[@]} -eq 0 ] && fixes=(airplane_off dnd_off)

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
repo_root=$(cd "$(dirname "$0")/../.." && pwd)
out_dir="$repo_root/traces/$ANDROID_SERIAL-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out_dir"
csv="$out_dir/trials.csv"
echo "fix,trial,condition,outcome,host_fixed,ms" >"$csv"

break_and_wait() {
    break_setting "$1" "$2" >/dev/null
    for _ in $(seq 1 20); do is_fixed "$1" || return 0; sleep 0.25; done
    echo "Could not break $1 over adb." >&2
    exit 1
}

set_condition() {
    sh_adb cmd statusbar collapse
    sh_adb input keyevent HOME
    case $1 in
        other_app) sh_adb am start -W -a android.settings.SETTINGS >/dev/null ;;
        shade_open) sh_adb cmd statusbar expand-notifications ;;
    esac
    sleep 1
}

run_trial() {
    local fix=$1 n=$2 condition=${CONDITIONS[$(($2 % ${#CONDITIONS[@]}))]}
    local id
    id="${fix}-${n}-$(date +%s%N | cut -c1-13)"
    break_and_wait "$fix" "$n"
    set_condition "$condition"
    sh_adb am broadcast -n "$RECEIVER" -a "$PKG.debug.RUN_ACTION" --es action "$fix" --es trialId "$id" >/dev/null
    read -r outcome ms < <(await_result "$id" "$out_dir")
    local host_fixed=0
    is_fixed "$fix" && host_fixed=1
    if [ "$outcome" = "verified" ] && [ $host_fixed -eq 0 ]; then outcome=FALSE_SUCCESS; fi
    echo "$fix,$n,$condition,$outcome,$host_fixed,$ms" >>"$csv"
    printf '  %-18s #%-2d %-10s %-14s %5s ms\n' "$fix" "$n" "$condition" "$outcome" "$ms"
    restore_device
}

summarize() {
    awk -F, 'NR > 1 {
        n[$1]++; count[$1 "," $4]++
        if ($4 == "verified") { ok[$1]++; t[$1, ok[$1]] = $6 }
        if ($4 == "FALSE_SUCCESS") fs[$1]++
    }
    END {
        z = 1.96
        for (a in n) {
            s = ok[a] + 0; m = n[a]; p = s / m
            d = 1 + z * z / m; c = (p + z * z / (2 * m)) / d
            h = z * sqrt(p * (1 - p) / m + z * z / (4 * m * m)) / d
            for (i = 1; i <= s; i++) v[i] = t[a, i]
            for (i = 2; i <= s; i++) for (j = i; j > 1 && v[j - 1] > v[j]; j--) { x = v[j]; v[j] = v[j - 1]; v[j - 1] = x }
            med = s == 0 ? "n/a" : (s % 2 ? v[(s + 1) / 2] : (v[s / 2] + v[s / 2 + 1]) / 2) " ms"
            printf "%-18s verified %d/%d (95%% Wilson %.0f-%.0f%%), false successes %d, median %s\n", a, s, m, 100 * (c - h), 100 * (c + h), fs[a] + 0, med
            for (k in count) { split(k, kk, ","); if (kk[1] == a) printf "    %-14s %d\n", kk[2], count[k] }
        }
    }' "$csv"
}

ensure_ready
save_device
# Leave the device as found even on early exit; airplane mode left on would also cut a tethered host's internet.
trap restore_device EXIT
sh_adb svc power stayon usb
echo "Device: $(sh_adb getprop ro.product.manufacturer) $(sh_adb getprop ro.product.model), SDK $(sh_adb getprop ro.build.version.sdk)"
echo "Traces: $out_dir"
for fix in "${fixes[@]}"; do
    for n in $(seq 1 "$trials"); do run_trial "$fix" "$n"; done
done
summarize | tee "$out_dir/summary.txt"
