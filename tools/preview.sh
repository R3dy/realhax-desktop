#!/usr/bin/env bash
# Headless visual test: apply install.sh (--skip-packages) to a throwaway HOME,
# start a real XFCE session on Xvfb, open alacritty running fastfetch, screenshot.
#   [REALHAX_ARGS="--lab-persona"] tools/preview.sh OUT.png [DISPLAY=:77] [WxH=1920x1080] [WAIT_SECONDS=18]
# Needs: Xvfb, xfce4, plank, conky, alacritty, fish (i.e. run install.sh once for real).
set -euo pipefail
OUT=$(realpath -m "$1"); DISP=${2:-:77}; RES=${3:-1920x1080}; WAIT=${4:-18}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
H=$(mktemp -d /tmp/realhax-preview.XXXXXX)
Xvfb "$DISP" -screen 0 "${RES}x24" -nolisten tcp +extension Composite +extension GLX >/dev/null 2>&1 &
XPID=$!; trap 'kill $XPID 2>/dev/null; sleep 0.5; rm -rf "$H"' EXIT
for _ in $(seq 50); do [[ -e /tmp/.X11-unix/X${DISP#:} ]] && break; sleep 0.1; done
env -i PATH="$PATH" USER="$USER" LANG="${LANG:-C.UTF-8}" HOME="$H" XDG_CONFIG_HOME="$H/.config" DISPLAY="$DISP" REALHAX_NO_PKILL=1 \
  dbus-run-session -- bash -c '
    set +e
    bash "'"$ROOT"'/install.sh" --skip-packages '"${REALHAX_ARGS:-}"' > "$HOME/install.log" 2>&1 || { echo "install failed:"; tail -20 "$HOME/install.log"; }
    XDG_CURRENT_DESKTOP=XFCE xfce4-session > "$HOME/session.log" 2>&1 &
    sleep 6
    XDG_CURRENT_DESKTOP=XFCE alacritty -o "window.position={x=140,y=230}" -e fish -l -c "clear; fastfetch; sleep 600" > "$HOME/alacritty.log" 2>&1 &
    sleep '"$WAIT"'
    /usr/bin/python3 -I -c "
import gi, sys; gi.require_version(\"Gdk\", \"3.0\"); from gi.repository import Gdk
w = Gdk.get_default_root_window(); pb = Gdk.pixbuf_get_from_window(w, 0, 0, w.get_width(), w.get_height())
pb.savev(sys.argv[1], \"png\", [], [])" "'"$OUT"'"
    grep -iE "error|warn|fail" "$HOME/install.log" | head -5
    cp "$HOME/install.log" "'"${OUT%.png}"'.install.log"; cp "$HOME/session.log" "'"${OUT%.png}"'.session.log" 2>/dev/null
  '
echo "screenshot: $OUT"
