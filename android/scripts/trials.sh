#!/usr/bin/env bash
# Runs M1 executor trials on one device over adb, cross-checks every result with an independent state read, and
# prints success counts, 95% Wilson intervals and median times per action.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/trials.sh [trials-per-action] [action ...]
#   actions: airplane_off dnd_off (default: both). Needs a debug build installed.
set -euo pipefail

PKG=com.rishikeshvk.unstuk
SERVICE=$PKG/.a11y.UnstukService
RECEIVER=$PKG/.debug.TrialReceiver
RESULT_TIMEOUT_S=40
CONDITIONS=(home other_app shade_open)

trials=${1:-20}
shift || true
actions=("$@")
[ ${#actions[@]} -eq 0 ] && actions=(airplane_off dnd_off)

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
repo_root=$(cd "$(dirname "$0")/../.." && pwd)
out_dir="$repo_root/traces/$ANDROID_SERIAL-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out_dir"
csv="$out_dir/trials.csv"
echo "action,trial,condition,outcome,host_off,ms" >"$csv"

sh_adb() { adb shell "$@" | tr -d '\r'; }

# Captures before grepping: with pipefail, grep -q closing the pipe early would fail the whole pipeline.
service_bound() {
    local dump
    dump=$(sh_adb dumpsys accessibility)
    grep -q 'Bound services:{Service\[label=Unstuk' <<<"$dump"
}

ensure_ready() {
    local window
    window=$(sh_adb dumpsys window)
    if grep -q 'isKeyguardShowing=true' <<<"$window"; then
        echo "Device is locked; unlock it and rerun." >&2
        exit 1
    fi
    if ! service_bound; then
        sh_adb settings put secure enabled_accessibility_services "$SERVICE"
        sh_adb settings put secure accessibility_enabled 1
        for _ in $(seq 1 20); do
            service_bound && break
            sleep 1
        done
    fi
    service_bound || {
        echo "Unstuk accessibility service did not bind." >&2
        exit 1
    }
    sh_adb cmd notification allow_dnd "$PKG"
}

is_off() {
    case $1 in
        airplane_off) [ "$(sh_adb settings get global airplane_mode_on)" = "0" ] ;;
        dnd_off) [ "$(sh_adb settings get global zen_mode)" = "0" ] ;;
    esac
}

# DND alternates between priority-only and total silence; both silence calls.
switch_on() {
    case $1 in
        airplane_off) sh_adb cmd connectivity airplane-mode enable ;;
        dnd_off) if [ $(($2 % 2)) -eq 0 ]; then sh_adb cmd notification set_dnd priority; else sh_adb cmd notification set_dnd on; fi ;;
    esac
    for _ in $(seq 1 20); do is_off "$1" || return 0; sleep 0.25; done
    echo "Could not switch the setting on for $1." >&2
    exit 1
}

switch_off_by_adb() {
    case $1 in
        airplane_off) sh_adb cmd connectivity airplane-mode disable ;;
        dnd_off) sh_adb cmd notification set_dnd off ;;
    esac
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

# Prints "<outcome> <elapsed ms>" from the trace, or "no_result 0" if none arrived in time.
await_result() {
    local trace
    for _ in $(seq 1 $((RESULT_TIMEOUT_S * 4))); do
        trace=$(sh_adb "run-as $PKG cat files/traces/$1.jsonl" 2>/dev/null || true)
        if grep -q '"step":"result"' <<<"$trace"; then
            printf '%s\n' "$trace" >"$out_dir/$1.jsonl"
            local first last outcome
            first=$(head -1 <<<"$trace" | sed -E 's/.*"ts":([0-9]+).*/\1/')
            last=$(grep '"step":"result"' <<<"$trace" | sed -E 's/.*"ts":([0-9]+).*/\1/')
            outcome=$(grep '"step":"result"' <<<"$trace" | sed -E 's/.*"outcome":"([a-z_]+)".*/\1/')
            echo "$outcome $((last - first))"
            return
        fi
        sleep 0.25
    done
    echo "no_result 0"
}

run_trial() {
    local action=$1 n=$2 condition=${CONDITIONS[$(($2 % ${#CONDITIONS[@]}))]}
    local id
    id="${action}-${n}-$(date +%s%N | cut -c1-13)"
    switch_on "$action" "$n"
    set_condition "$condition"
    sh_adb am broadcast -n "$RECEIVER" -a "$PKG.debug.RUN_ACTION" --es action "$action" --es trialId "$id" >/dev/null
    read -r outcome ms < <(await_result "$id")
    local host_off=0
    is_off "$action" && host_off=1
    if [ "$outcome" = "verified" ] && [ $host_off -eq 0 ]; then outcome=FALSE_SUCCESS; fi
    echo "$action,$n,$condition,$outcome,$host_off,$ms" >>"$csv"
    printf '  %-12s #%-2d %-10s %-14s %5s ms\n' "$action" "$n" "$condition" "$outcome" "$ms"
    [ $host_off -eq 1 ] || switch_off_by_adb "$action"
    sh_adb cmd statusbar collapse
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
            printf "%-12s verified %d/%d (95%% Wilson %.0f-%.0f%%), false successes %d, median %s\n", a, s, m, 100 * (c - h), 100 * (c + h), fs[a] + 0, med
            for (k in count) { split(k, kk, ","); if (kk[1] == a) printf "    %-14s %d\n", kk[2], count[k] }
        }
    }' "$csv"
}

ensure_ready
# Leave the device as found even on early exit; airplane mode left on would also cut a tethered host's internet.
stay_on_before=$(sh_adb settings get global stay_on_while_plugged_in)
restore_device() {
    sh_adb cmd connectivity airplane-mode disable || true
    sh_adb cmd notification set_dnd off || true
    sh_adb settings put global stay_on_while_plugged_in "$stay_on_before" || true
}
trap restore_device EXIT
sh_adb svc power stayon usb
echo "Device: $(sh_adb getprop ro.product.manufacturer) $(sh_adb getprop ro.product.model), SDK $(sh_adb getprop ro.build.version.sdk)"
echo "Traces: $out_dir"
for action in "${actions[@]}"; do
    for n in $(seq 1 "$trials"); do run_trial "$action" "$n"; done
done
summarize | tee "$out_dir/summary.txt"
