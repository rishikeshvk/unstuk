#!/usr/bin/env bash
# Puts the signed release build through the paths R8 can break: launch, the model's first decision, and one fix
# on each of the direct and accessibility rungs, checked on screen and by an independent adb read. The debug
# scripts can't cover this: release has no debug receivers and runs R8-optimized code.
#
# Usage: ANDROID_SERIAL=<serial> android/scripts/release-smoke.sh
#   Needs the release signing properties (see README) and the device unlocked. Reinstalls the app over the
#   current release build and turns its accessibility service back on; settings are restored on exit.
set -euo pipefail

source "$(dirname "$0")/device.sh"

# fix | complaint | step line the fixed reply shows for the fix's rung
# The complaints are e2e.sh's fixtures, not real user messages (invariant 9).
CASES=(
    "brightness_up|Screen is too dark|Changed the setting directly"
    "inversion_off|Screen went black and white and colours are inverted|Tapped the switch for you"
)
REPLY_TIMEOUT_S=20

: "${ANDROID_SERIAL:?Set ANDROID_SERIAL to the target device}"
export ANDROID_SERIAL
android_dir="$(cd "$(dirname "$0")/.." && pwd)"
apk="$android_dir/app/build/outputs/apk/release/app-release.apk"

failures=0
pass() { echo "PASS $1"; }
fail() {
    echo "FAIL $1" >&2
    failures=$((failures + 1))
}

install_release() {
    (cd "$android_dir" && ./gradlew -q assembleRelease)
    local out
    out=$(adb install -r "$apk" 2>&1) && return
    echo "$out" >&2
    if grep -q INSTALL_FAILED_UPDATE_INCOMPATIBLE <<<"$out"; then
        echo "The installed Unstuk is signed with another key, likely a debug build. Uninstalling it clears its" \
            "data and grants, so do that yourself, then rerun." >&2
    fi
    exit 1
}

check_launch() {
    # A cleared task (NEW_TASK | CLEAR_TASK) gives a fresh home screen without a force-stop, which would make the
    # system drop the accessibility service from the enabled list.
    sh_adb am start -W -f 0x10008000 -n "$PKG/.MainActivity" >/dev/null
    sleep 2
    if [ -n "$(sh_adb pidof "$PKG")" ]; then pass "launch"; else fail "launch"; fi
}

# The setup card shows while the service is off, and every screen read turns it off, so the card would come and
# go under the taps. Dismissed once, it stays hidden while the activity lives; cases return home with Done.
dismiss_banner() {
    sh_adb settings delete secure enabled_accessibility_services >/dev/null
    await_text "Set up" 10
    tap 'content-desc="Dismiss"'
    ensure_ready
}

# Watches the setting over adb rather than the screen: a screen read mid-fix would suspend the service doing it.
await_fix() {
    local deadline=$((SECONDS + $2))
    while [ "$SECONDS" -lt "$deadline" ]; do
        is_fixed "$1" && return 0
        sleep 0.5
    done
    return 1
}

# An accessibility fix ends by leaving Quick Settings; the screen is read once Unstuk is in front again.
await_app_in_front() {
    local window
    for _ in $(seq 1 20); do
        window=$(sh_adb dumpsys window)
        grep -q "mCurrentFocus=.*$PKG/" <<<"$window" && return 0
        sleep 0.25
    done
    return 1
}

run_case() {
    local fix complaint step
    IFS='|' read -r fix complaint step <<<"$1"
    break_setting "$fix" 0 >/dev/null
    # One screen read for both taps, since each read suspends the accessibility service for a moment.
    dump_screen
    local field help
    field=$(centre_in_dump 'class="android.widget.EditText"')
    help=$(centre_in_dump 'text="Help me"')
    # shellcheck disable=SC2086 # x and y are separate arguments
    sh_adb input tap $field
    # input text ends a word at each space, so spaces are sent as %s.
    sh_adb input text "${complaint// /%s}"
    hide_keyboard
    # shellcheck disable=SC2086
    sh_adb input tap $help
    if ! await_fix "$fix" "$REPLY_TIMEOUT_S"; then
        fail "$fix: the setting was not changed within ${REPLY_TIMEOUT_S} s"
    elif ! await_app_in_front || ! await_text "I checked, and it worked." 10; then
        fail "$fix: the setting changed, but no fixed reply"
    elif ! tap 'text="How I fixed it"' || ! await_text "$step" 3; then
        fail "$fix: fixed, but not by its rung (\"$step\" missing)"
    else
        pass "$fix"
    fi
    restore_device
    tap 'text="Done"'
}

check_crashes() {
    local crashes
    crashes=$(sh_adb logcat -b crash -d | grep -F "$PKG" || true)
    if [ -z "$crashes" ]; then
        pass "no crashes"
    else
        fail "crashed"
        sh_adb logcat -b crash -d | grep -E "FATAL|Abort message|Caused by" | head -10 >&2
    fi
}

# Runs on every exit, so a crash that stops a case midway is still reported.
finish() {
    local status=$?
    check_crashes
    restore_device
    sh_adb settings put global animator_duration_scale "$animator"
    if [ "$status" -ne 0 ] || [ "$failures" -ne 0 ]; then
        echo "Release smoke test failed." >&2
        exit 1
    fi
    echo "Release smoke test passed."
}

install_release
ensure_ready
save_device
animator=$(sh_adb settings get global animator_duration_scale)
trap finish EXIT
# With animations off the app snaps each screen to its end state, and uiautomator can read the screen.
sh_adb settings put global animator_duration_scale 0
sh_adb logcat -b crash -c
check_launch
dismiss_banner
for case in "${CASES[@]}"; do run_case "$case"; done
