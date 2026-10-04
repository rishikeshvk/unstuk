#!/usr/bin/env bash
# Runs one scripted complaint per case through the whole pipeline (matcher, gate, diagnosis, executor,
# verification) on one device. Each case breaks a setting over adb, sends the complaint, and compares the last
# reply with the expected one; a "verified" reply must also pass an independent adb read of the fix.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/e2e.sh [case name ...]   (default: all cases)
#   Needs a debug build installed. Cases that touch airplane mode or mobile data cut a tethered host offline
#   for a few seconds; the device is restored after every case and on exit.
set -euo pipefail

source "$(dirname "$0")/device.sh"
RECEIVER=$PKG/.debug.ComplaintReceiver

# name | fixes to break first, joined by + (or -) | complaint | broadcast extras | expected reply | fix the host checks (or -)
# The complaints are fixtures written for this script, not real user messages (invariant 9).
CASES=(
    "no_internet_airplane|airplane_off|My internet is not working||verified|airplane_off"
    "no_internet_data|wifi_on+mobile_data_on|Mobile data not working||verified|mobile_data_on"
    "wifi_no_load|auto_time_on|Wifi connected but pages don't load||verified|auto_time_on"
    "not_ringing_dnd|dnd_off|Phone doesn't ring||verified|dnd_off"
    "not_ringing_ringer|ringer_normal|Phone doesn't ring||verified|ringer_normal"
    "cant_hear_call|call_volume_up|I can't hear the person||verified|call_volume_up"
    "notifications_data_saver|data_saver_off|WhatsApp messages come late||verified|data_saver_off"
    "talkback_on|talkback_off|Phone keeps talking to me|--ez confirm true|verified|talkback_off"
    "colours_wrong|inversion_off|Screen went black and white and colours are inverted||verified|inversion_off"
    "screen_too_dim|brightness_up|Screen is too dark||verified|brightness_up"
    "screen_off_fast|timeout_longer|Screen goes off quickly||verified|timeout_longer"
    "wont_rotate|rotation_unlock|Screen won't go sideways||verified|rotation_unlock"
    "text_too_small|font_size_settings|Letters are tiny||verified|font_size_settings"
    "bluetooth|bluetooth_on|My earbuds won't pair||verified|bluetooth_on"
    "app_permission|-|Camera not working in Zoom||all_clear|-"
    "wrong_time|auto_time_on|The clock shows the wrong time||verified|auto_time_on"
    "reset_network|-|Please reset network settings||guide|-"
    "gate_confirm|auto_time_on|My internet clock shows the wrong time||confirm|-"
    "gate_clarify|-|Dark colours and small||clarify|-"
    "gate_decline|-|What is the capital of France||decline|-"
)

# The panel rung waits for the user; this plays the user's tap after the screen has opened.
user_taps() {
    case $1 in
        font_size_settings) sleep 3 && sh_adb settings put system font_scale 1.15 ;;
    esac
}

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
repo_root=$(cd "$(dirname "$0")/../.." && pwd)
out_dir="$repo_root/traces/e2e-$ANDROID_SERIAL-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out_dir"
csv="$out_dir/e2e.csv"
echo "case,expected,reply,host_fixed,verdict,ms" >"$csv"

run_case() {
    local name broken complaint extras expected checked
    IFS='|' read -r name broken complaint extras expected checked <<<"$1"
    local id="e2e-${name}-$(date +%s%N | cut -c1-13)"
    sh_adb input keyevent HOME
    local fix
    for fix in ${broken//+/ }; do [ "$fix" = "-" ] || break_setting "$fix" 0 >/dev/null; done
    sleep 1
    # adb shell re-parses its arguments on the device, so the complaint is single-quoted for that shell.
    local quoted=${complaint//\'/\'\\\'\'}
    # shellcheck disable=SC2086 # extras are separate adb arguments
    sh_adb am broadcast -n "$RECEIVER" -a "$PKG.debug.RUN_COMPLAINT" \
        --es complaint "'$quoted'" --es trialId "$id" $extras >/dev/null
    user_taps "$checked"
    read -r reply ms < <(await_result "$id" "$out_dir")
    local host_fixed=-
    if [ "$checked" != "-" ]; then
        host_fixed=0
        is_fixed "$checked" && host_fixed=1
    fi
    local verdict=pass
    if [ "$reply" != "$expected" ]; then verdict=FAIL; fi
    if [ "$reply" = "verified" ] && [ "$host_fixed" != "1" ]; then verdict=FALSE_SUCCESS; fi
    echo "$name,$expected,$reply,$host_fixed,$verdict,$ms" >>"$csv"
    printf '  %-26s expected %-10s got %-14s host %-2s %-13s %6s ms\n' \
        "$name" "$expected" "$reply" "$host_fixed" "$verdict" "$ms"
    restore_device
}

ensure_ready
save_device
trap restore_device EXIT
sh_adb svc power stayon usb
echo "Device: $(sh_adb getprop ro.product.manufacturer) $(sh_adb getprop ro.product.model), SDK $(sh_adb getprop ro.build.version.sdk)"
echo "Traces: $out_dir"
for entry in "${CASES[@]}"; do
    name=${entry%%|*}
    if [ $# -eq 0 ] || [[ " $* " == *" $name "* ]]; then run_case "$entry"; fi
done
awk -F, 'NR > 1 { n++; if ($5 == "pass") ok++; if ($5 == "FALSE_SUCCESS") fs++ }
    END { printf "passed %d/%d, false successes %d\n", ok, n, fs }' "$csv" | tee "$out_dir/summary.txt"
