#!/usr/bin/env bash
# Records the README's demo video: three complaints typed into the app, each recorded until its reply settles,
# then captioned and joined into one MP4 for GitHub's video player. The device is left as found.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/demo.sh
#   Needs the release build installed and the device unlocked. No scene touches airplane mode or mobile data.
#   Refuses to run while any app has a notification. Writes android/build/demo/unstuk-demo.mp4; watch it
#   before uploading it anywhere.
set -euo pipefail

source "$(dirname "$0")/device.sh"

# name | fix to break first (or -) | complaint | seconds to record after "Help me" | caption
# The complaints are e2e.sh's and screenshots.sh's fixtures, not real user messages (invariant 9).
SCENES=(
    "direct|dnd_off|Phone doesn't ring|3|Fixed directly, then checked"
    "accessibility|bluetooth_on|My earbuds won't pair|12|Unstuk taps the switch for you"
    "decline|-|can you book me a cab to the station|2|Out of scope: no guess, no action"
)
WIDTH=540
CROSSFADE_S=0.4
HOLD_S=1.5
MAX_BYTES=$((10 * 1024 * 1024)) # GitHub's limit for a video attachment
INK=0x1F1B2E
GROUND=0xF6F1EA

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
android_dir="$(cd "$(dirname "$0")/.." && pwd)"
font="$android_dir/app/src/main/res/font/figtree_semibold.ttf"
out_dir="$android_dir/build/demo"
mkdir -p "$out_dir"

night=$(sh_adb cmd uimode night | sed -nE 's/Night mode: (.*)/\1/p')
animator=$(sh_adb settings get global animator_duration_scale)
touches=$(sh_adb settings get system show_touches)
demo_allowed=$(sh_adb settings get global sysui_demo_allowed)

# A fix that opens Quick Settings shows the notification shade on the way, and the video is public.
# The system's own (USB debugging, tethering) say nothing private; anything from an app could.
refuse_app_notifications() {
    local apps
    apps=$(sh_adb cmd notification list | cut -d'|' -f2 | grep -vx android | sort -u || true)
    [ -z "$apps" ] && return 0
    echo "Notifications from these apps would show in the video: $(tr '\n' ' ' <<<"$apps")" >&2
    echo "Clear them on the phone, then rerun." >&2
    exit 1
}

demo_mode() { sh_adb am broadcast -a com.android.systemui.demo -e command "$@" >/dev/null; }

restore() {
    sh_adb pkill -INT screenrecord || true
    demo_mode exit || true
    restore_device
    sh_adb cmd uimode night "$night" >/dev/null
    sh_adb settings put global animator_duration_scale "$animator"
    sh_adb settings put system show_touches "$touches"
    sh_adb settings put global sysui_demo_allowed "$demo_allowed"
}

# A fresh task rather than a force-stop: stopping the app also disconnects its accessibility service.
open_app() {
    sh_adb am start -W -f 0x10008000 -n "$PKG/.MainActivity" >/dev/null
    sleep 1.5
}

# hide_keyboard presses Back, which would close the app if the keyboard hadn't opened yet.
tap_field() {
    local ime
    # shellcheck disable=SC2086 # x and y are separate arguments
    sh_adb input tap $field
    for _ in $(seq 1 20); do
        ime=$(sh_adb dumpsys input_method)
        grep -q 'mInputShown=true' <<<"$ime" && return 0
        sleep 0.25
    done
    echo "The keyboard did not open." >&2
    return 1
}

# The empty field's hint types forever, so with animations on the screen never goes idle for uiautomator; and a
# screen read suspends Unstuk's service, which a fix may need. So both taps are measured once, before recording.
measure_taps() {
    sh_adb settings put global animator_duration_scale 0
    # A screen read suspends the service, so the app shows its access banner during the read and everything
    # below it moves down. With the service off the banner stays put and can be dismissed for this screen,
    # leaving the layout the recording sees once the service is back on.
    sh_adb settings delete secure enabled_accessibility_services >/dev/null
    open_app
    tap 'content-desc="Dismiss"'
    field=$(centre_of 'class="android.widget.EditText"')
    [ -n "$field" ] || { echo "Could not find the complaint field." >&2; exit 1; }
    tap_field
    sh_adb input text x
    hide_keyboard
    help_me=$(centre_of 'text="Help me"')
    [ -n "$help_me" ] || { echo "Could not find Help me." >&2; exit 1; }
    sh_adb settings put global animator_duration_scale 1
    ensure_ready
}

clean_status_bar() {
    sh_adb settings put global sysui_demo_allowed 1
    demo_mode enter
    demo_mode clock -e hhmm 1200
    demo_mode battery -e level 100 -e plugged false
    demo_mode network -e wifi hide -e mobile show -e level 4 -e datatype none
    demo_mode notifications -e visible false
}

# Word by word, so the complaint reads as typed rather than pasted.
type_slowly() {
    local words word i
    read -ra words <<<"$1"
    for i in "${!words[@]}"; do
        word=${words[i]//\'/\\\'}
        if [ "$i" -lt $((${#words[@]} - 1)) ]; then word="$word%s"; fi
        sh_adb input text "$word"
        sleep 0.15
    done
}

# Interrupting screenrecord makes it finish the file; the file is only complete once the process has gone.
stop_recording() {
    sh_adb pkill -INT screenrecord
    for _ in $(seq 1 60); do
        sh_adb pidof screenrecord >/dev/null || return 0
        sleep 0.25
    done
    sh_adb pkill -KILL screenrecord || true
    return 1
}

now() { date +%s.%N; }

# One attempt at a scene. Fails when screenrecord hangs or its clip ends before the tap: on the Moto it
# sometimes stops getting frames partway through, and that never reproduced outside a full scene.
take() {
    local name=$1 broken=$2 complaint=$3 wait_s=$4 started tapped duration
    [ "$broken" = "-" ] || break_setting "$broken" 0 >/dev/null
    await_service
    # SystemUI leaves demo mode on its own between scenes, so each scene enters it again.
    clean_status_bar
    open_app
    # Detached on the device, so the recording doesn't depend on this adb session staying up.
    sh_adb "nohup screenrecord --bit-rate 8000000 /sdcard/demo-$name.mp4 >/dev/null 2>&1 &"
    started=$(now)
    # Typing starts soon after the clip does: the empty field's animated hint reads like a complaint left unsent.
    sleep 0.5
    # Checked by hand: inside "if take", set -e is off, and Back without a keyboard would close the app.
    tap_field || { stop_recording || true; return 1; }
    type_slowly "$complaint"
    sleep 0.4
    hide_keyboard
    # shellcheck disable=SC2086
    sh_adb input tap $help_me
    tapped=$(now)
    sleep "$wait_s"
    stop_recording || { echo "screenrecord hung during $name." >&2; return 1; }
    adb pull "/sdcard/demo-$name.mp4" "$out_dir/$name.raw.mp4" >/dev/null
    sh_adb rm "/sdcard/demo-$name.mp4"
    duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out_dir/$name.raw.mp4")
    # A still reply adds no frames, so a healthy clip can end just after the tap's transition; a stalled one
    # ends during the typing.
    awk -v d="$duration" -v s="$started" -v t="$tapped" 'BEGIN { exit !(d >= t - s + 0.3) }' || {
        echo "The $name clip stops at ${duration}s, before Help me was tapped." >&2
        return 1
    }
}

record() {
    local name broken complaint wait_s caption attempt
    IFS='|' read -r name broken complaint wait_s caption <<<"$1"
    for attempt in 1 2 3; do
        if take "$name" "$broken" "$complaint" "$wait_s"; then
            restore_device
            printf '%s' "$caption" >"$out_dir/$name.caption.txt"
            echo "recorded $name"
            return 0
        fi
        restore_device
        echo "Retrying $name ($attempt of 3 failed)." >&2
    done
    echo "Could not record $name." >&2
    exit 1
}

# Scales each clip, burns its caption into a band over the navigation bar, and crossfades the clips together.
assemble() {
    local inputs=() filters="" offset=0 previous="v0" i=0 scene name duration
    for scene in "${SCENES[@]}"; do
        name=${scene%%|*}
        inputs+=(-i "$out_dir/$name.raw.mp4")
        # screenrecord writes no frames while the screen is still, so the settled reply is held for HOLD_S.
        filters+="[$i:v]fps=30,tpad=stop_mode=clone:stop_duration=$HOLD_S,scale=$WIDTH:-2,settb=AVTB,"
        filters+="drawbox=y=ih-96:w=iw:h=96:color=$INK:t=fill,"
        filters+="drawtext=fontfile=$font:textfile=$out_dir/$name.caption.txt:fontsize=26:fontcolor=$GROUND:"
        filters+="x=(w-text_w)/2:y=h-48-text_h/2[v$i];"
        i=$((i + 1))
    done
    for i in $(seq 1 $((${#SCENES[@]} - 1))); do
        name=${SCENES[i - 1]%%|*}
        duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out_dir/$name.raw.mp4")
        offset=$(awk -v o="$offset" -v d="$duration" -v h="$HOLD_S" -v f="$CROSSFADE_S" 'BEGIN { print o + d + h - f }')
        filters+="[$previous][v$i]xfade=transition=fade:duration=$CROSSFADE_S:offset=$offset[x$i];"
        previous="x$i"
    done
    ffmpeg -v error -y "${inputs[@]}" -filter_complex "${filters%;}" -map "[$previous]" \
        -c:v libx264 -crf 28 -preset slow -pix_fmt yuv420p -movflags +faststart -an "$out_dir/unstuk-demo.mp4"
    local bytes
    bytes=$(stat -c %s "$out_dir/unstuk-demo.mp4")
    [ "$bytes" -lt "$MAX_BYTES" ] || { echo "The video is $bytes bytes, over GitHub's 10 MB limit." >&2; exit 1; }
    echo "wrote $out_dir/unstuk-demo.mp4 ($bytes bytes)"
}

ensure_ready
refuse_app_notifications
save_device
trap restore EXIT
sh_adb cmd uimode night no >/dev/null
measure_taps
for scene in "${SCENES[@]}"; do record "$scene"; done
assemble
