# Device helpers shared by trials.sh and e2e.sh: adb access, readiness, and per-fix ways to break a setting
# over adb and to read it back independently of the app. Source it; it does nothing on its own.

PKG=com.rishikeshvk.unstuk
SERVICE=$PKG/.a11y.UnstukService
TALKBACK=com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService
RESULT_TIMEOUT_S=40

# Waits first: toggling Data Saver or tethering re-enumerates USB, and adb is gone for a second or two.
sh_adb() {
    adb wait-for-device
    adb shell "$@" | tr -d '\r'
}

# The shell's volume command is ignored on the Moto, so the app's debug receiver sets audio state instead.
set_audio() { sh_adb am broadcast -n "$PKG/.debug.AudioSetupReceiver" -a "$PKG.debug.SET_AUDIO" "$@" >/dev/null; }

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
    sh_adb appops set "$PKG" WRITE_SETTINGS allow
}

stream_volume() { sh_adb cmd media_session volume --stream "$1" --get | sed -nE 's/.*volume is ([0-9]+).*/\1/p'; }
stream_max() { sh_adb cmd media_session volume --stream "$1" --get | sed -nE 's/.*\.\.([0-9]+)\].*/\1/p'; }

# Settings that breaking and restoring touch, saved once so the device is left as found.
SAVED_KEYS=(
    "system screen_brightness" "system screen_brightness_mode" "system screen_off_timeout"
    "system accelerometer_rotation" "system font_scale" "global auto_time"
    "secure enabled_accessibility_services" "secure accessibility_display_inversion_enabled"
)
declare -A SAVED
save_device() {
    local key
    for key in "${SAVED_KEYS[@]}"; do SAVED[$key]=$(sh_adb settings get $key); done
    SAVED[ring]=$(stream_volume 2)
    SAVED[call]=$(stream_volume 0)
    SAVED[stay_on]=$(sh_adb settings get global stay_on_while_plugged_in)
    SAVED[wifi]=$(sh_adb settings get global wifi_on)
    SAVED[bluetooth]=$(sh_adb settings get global bluetooth_on)
    # Mobile data is stored per SIM, keyed by the default data subscription.
    SAVED[data]=$(sh_adb settings get global "mobile_data$(sh_adb settings get global multi_sim_data_call)")
}

# Airplane mode and mobile data first: the Moto is this machine's internet connection. Radios go back to how
# save_device found them, not to "on".
restore_device() {
    sh_adb cmd connectivity airplane-mode disable || true
    sh_adb svc data enable || true
    [ "${SAVED[data]}" = "1" ] || sh_adb svc data disable || true
    if [ "${SAVED[wifi]}" = "0" ]; then sh_adb svc wifi disable || true; else sh_adb svc wifi enable || true; fi
    if [ "${SAVED[bluetooth]}" = "1" ]; then
        sh_adb cmd bluetooth_manager enable >/dev/null || true
    else
        sh_adb cmd bluetooth_manager disable >/dev/null || true
    fi
    sh_adb cmd notification set_dnd off || true
    sh_adb cmd netpolicy set restrict-background false >/dev/null || true
    local key
    for key in "${SAVED_KEYS[@]}"; do
        if [ "${SAVED[$key]}" = "null" ]; then
            sh_adb settings delete $key >/dev/null || true
        else
            sh_adb settings put $key "${SAVED[$key]}" || true
        fi
    done
    set_audio --ei ringer 2 || true
    set_audio --ei stream 2 --ei index "${SAVED[ring]}" || true
    set_audio --ei stream 0 --ei index "${SAVED[call]}" || true
    sh_adb settings put global stay_on_while_plugged_in "${SAVED[stay_on]}" || true
    sh_adb cmd statusbar collapse || true
}

# Puts the device in the state <fix> repairs. <n> varies the variant where a fix has more than one.
break_setting() {
    case $1 in
        airplane_off) sh_adb cmd connectivity airplane-mode enable ;;
        dnd_off) if [ $(($2 % 2)) -eq 0 ]; then sh_adb cmd notification set_dnd priority; else sh_adb cmd notification set_dnd on; fi ;;
        mobile_data_on) sh_adb svc data disable ;;
        wifi_on) sh_adb svc wifi disable ;;
        data_saver_off) sh_adb cmd netpolicy set restrict-background true ;;
        auto_time_on) sh_adb settings put global auto_time 0 ;;
        ringer_normal) set_audio --ei ringer 1 ;;
        ring_volume_up) set_audio --ei stream 2 --ei index 0 ;;
        call_volume_up) set_audio --ei stream 0 --ei index 1 ;;
        talkback_off) sh_adb settings put secure enabled_accessibility_services "$SERVICE:$TALKBACK" ;;
        inversion_off) sh_adb settings put secure accessibility_display_inversion_enabled 1 ;;
        brightness_up) sh_adb settings put system screen_brightness_mode 0 && sh_adb settings put system screen_brightness 5 ;;
        timeout_longer) sh_adb settings put system screen_off_timeout 15000 ;;
        rotation_unlock) sh_adb settings put system accelerometer_rotation 0 ;;
        font_size_settings) sh_adb settings put system font_scale 1.0 ;;
        bluetooth_on) sh_adb cmd bluetooth_manager disable ;;
        *) echo "No way to break $1 over adb." >&2; return 1 ;;
    esac
}

# An independent read of whether <fix> took effect, using adb only.
is_fixed() {
    case $1 in
        airplane_off) [ "$(sh_adb settings get global airplane_mode_on)" = "0" ] ;;
        dnd_off) [ "$(sh_adb settings get global zen_mode)" = "0" ] ;;
        mobile_data_on) [ "$(sh_adb settings get global "mobile_data$(sh_adb settings get global multi_sim_data_call)")" = "1" ] ;;
        wifi_on) [ "$(sh_adb settings get global wifi_on)" != "0" ] ;;
        data_saver_off) sh_adb cmd netpolicy get restrict-background | grep -q disabled ;;
        auto_time_on) [ "$(sh_adb settings get global auto_time)" = "1" ] ;;
        ringer_normal) [ "$(sh_adb settings get global mode_ringer)" = "2" ] ;;
        ring_volume_up) [ "$(stream_volume 2)" -gt 0 ] ;;
        call_volume_up) [ $(($(stream_volume 0) * 2)) -ge "$(stream_max 0)" ] ;;
        talkback_off) ! sh_adb settings get secure enabled_accessibility_services | grep -q talkback ;;
        inversion_off) [ "$(sh_adb settings get secure accessibility_display_inversion_enabled)" = "0" ] ;;
        brightness_up) [ "$(sh_adb settings get system screen_brightness)" -ge 26 ] ;;
        timeout_longer) [ "$(sh_adb settings get system screen_off_timeout)" -ge 30000 ] ;;
        rotation_unlock) [ "$(sh_adb settings get system accelerometer_rotation)" = "1" ] ;;
        font_size_settings) awk -v s="$(sh_adb settings get system font_scale)" 'BEGIN { exit !(s > 1.0) }' ;;
        bluetooth_on) [ "$(sh_adb settings get global bluetooth_on)" = "1" ] ;;
        *) return 1 ;;
    esac
}

# The host's read after an app-verified change: some settings (mode_ringer) are persisted about a second after
# the system applies them, so allow 3 s for the record to catch up.
host_confirms() {
    for _ in $(seq 1 12); do
        is_fixed "$1" && return 0
        sleep 0.25
    done
    return 1
}

# Prints "<outcome> <elapsed ms>" from trace <id>, copying it to <out dir>, or "no_result 0" if none arrived.
await_result() {
    local trace
    for _ in $(seq 1 $((RESULT_TIMEOUT_S * 4))); do
        trace=$(sh_adb "run-as $PKG cat files/traces/$1.jsonl" 2>/dev/null || true)
        if grep -q '"step":"result"' <<<"$trace"; then
            printf '%s\n' "$trace" >"$2/$1.jsonl"
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
