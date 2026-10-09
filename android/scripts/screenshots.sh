#!/usr/bin/env bash
# Takes the write-up's app screenshots (M9 spec section 5): types four complaints into the app and captures the
# reply each one gets. The device is left as found: settings, light or dark mode, and animation speed.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/screenshots.sh
#   Needs a debug build installed and the device unlocked. No case touches airplane mode or mobile data.
set -euo pipefail

source "$(dirname "$0")/device.sh"

# name | fix to break first (or -) | complaint | seconds to wait for the reply
# The complaints are fixtures written for this script, not real user messages (invariant 9).
# Each was checked on the Moto, whose state text moves the model's confidence: the confirm band is 0.70 to 0.75.
SHOTS=(
    "fixed|ringer_normal|my phone doesnt ring anymore|10"
    "confirm|ring_volume_up|my phone is too quiet|6"
    "clarify|inversion_off|the screen looks strange|6"
    "decline|-|can you book me a cab to the station|6"
)
WIDTH=540

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
out_dir="$(cd "$(dirname "$0")/../.." && pwd)/docs/figures/screens"
mkdir -p "$out_dir"

night=$(sh_adb cmd uimode night | sed -nE 's/Night mode: (.*)/\1/p')
animator=$(sh_adb settings get global animator_duration_scale)
restore() {
    restore_device
    sh_adb cmd uimode night "$night" >/dev/null
    sh_adb settings put global animator_duration_scale "$animator"
}

shoot() {
    local name broken complaint wait_s
    IFS='|' read -r name broken complaint wait_s <<<"$1"
    [ "$broken" = "-" ] || break_setting "$broken" 0 >/dev/null
    sh_adb am force-stop "$PKG"
    sh_adb am start -W -n "$PKG/.MainActivity" >/dev/null
    sleep 2
    tap 'class="android.widget.EditText"'
    # input text ends a word at each space, so spaces are sent as %s.
    sh_adb input text "${complaint// /%s}"
    hide_keyboard
    tap 'text="Help me"'
    sleep "$wait_s"
    adb exec-out screencap -p >"$out_dir/$name.full.png"
    magick "$out_dir/$name.full.png" -resize "${WIDTH}x" -strip "$out_dir/$name.png"
    rm "$out_dir/$name.full.png"
    echo "wrote $out_dir/$name.png"
    restore_device
}

ensure_ready
save_device
trap restore EXIT
sh_adb cmd uimode night no >/dev/null
# With animations off the app snaps each screen to its end state, and uiautomator can read the screen.
sh_adb settings put global animator_duration_scale 0
for shot in "${SHOTS[@]}"; do shoot "$shot"; done
