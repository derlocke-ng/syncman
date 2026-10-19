#!/usr/bin/env bash
# installer for syncman — kiwi convention: ./install.sh install|update|uninstall [--purge]
#
# User scope ONLY: syncman manages per-user systemd services and per-user data.
#
#   <prefix>/bin/syncman, syncjob, syncman-panel
#   ~/.config/systemd/user/syncjob@.service   one template unit, one instance per job
#   ~/.config/syncman/                        config + jobs — kept unless --purge
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-install}"

[[ "${KIWI_SCOPE:-user}" == "user" ]] || {
    echo "error: syncman is user-only (SCOPES=user)" >&2; exit 1; }

APP_ID=eu.kiwinetwork.Syncman
PREFIX="${KIWI_PREFIX:-$HOME/.local}"
BIN="$PREFIX/bin"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/syncman"

say() { printf ':: %s\n' "$*"; }

# no user bus (a bare ssh session, a container) must not fail the install
sysd() { systemctl --user "$@" 2>/dev/null || true; }

# kiwi exports KIWI_GUI=0/1; standalone installs fall back to checking for
# the GTK4 stack, the same test kiwi uses
want_gui() {
    [[ ${KIWI_GUI:-} == 0 ]] && return 1
    [[ -n ${KIWI_GUI:-} ]] && return 0
    [[ -e /usr/lib64/girepository-1.0/Gtk-4.0.typelib ||
       -e /usr/lib/girepository-1.0/Gtk-4.0.typelib ]]
}

refresh_desktop() {
    command -v gtk-update-icon-cache >/dev/null 2>&1 && \
        gtk-update-icon-cache -qtf "$DATA_HOME/icons/hicolor" 2>/dev/null || true
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database -q "$APPS" 2>/dev/null || true
}

do_install() {
    say "installing syncman + syncjob to $BIN"
    install -Dm755 "$SRC/bin/syncman" "$BIN/syncman"
    install -Dm755 "$SRC/bin/syncjob" "$BIN/syncjob"

    # the Nova Network edition installed its entry under another id
    rm -f "$APPS/org.novanetwork.Syncman.desktop"

    if want_gui; then
        say "installing syncman-panel + desktop entry + icon"
        install -Dm755 "$SRC/gui/syncman-panel" "$BIN/syncman-panel"
        mkdir -p "$APPS"
        sed "s|^Exec=.*|Exec=$BIN/syncman-panel|" "$SRC/data/syncman-panel.desktop" \
            > "$APPS/$APP_ID.desktop"
        install -Dm644 "$SRC/data/syncman.svg" "$ICON_DIR/$APP_ID.svg"
        refresh_desktop
    else
        say "no GTK4 stack (or KIWI_GUI=0) — skipping panel"
    fi

    say "installing service template"
    mkdir -p "$UNIT_DIR"
    # point the template at the actual install prefix
    sed "s|^ExecStart=.*|ExecStart=$BIN/syncjob %i|" "$SRC/data/syncjob@.service" \
        > "$UNIT_DIR/syncjob@.service"
    sysd daemon-reload

    mkdir -p "$CONF_DIR/jobs"
    [[ -f "$CONF_DIR/syncman.conf" ]] || cat > "$CONF_DIR/syncman.conf" <<'CONF'
# syncman configuration
# seconds between sync passes:
INTERVAL=30
# where the .job files live (point at a Nextcloud-synced folder to share
# job definitions across machines):
#JOBS_DIR=~/Nextcloud/syncman-jobs
CONF
    say "done — try: syncman add <name>  |  syncman list  |  syncman-panel"
}

do_update() {
    do_install
    # running jobs keep the old worker process until restarted
    sysd try-restart 'syncjob@*.service'
    say "restarted running sync jobs"
}

do_uninstall() {
    say "stopping all sync jobs"
    local u
    for u in $(systemctl --user list-units 'syncjob@*.service' --all --plain --no-legend 2>/dev/null | awk '{print $1}'); do
        sysd disable --now "$u"
    done
    rm -f "$BIN/syncman" "$BIN/syncjob" "$BIN/syncman-panel" \
          "$APPS/$APP_ID.desktop" "$APPS/org.novanetwork.Syncman.desktop" \
          "$ICON_DIR/$APP_ID.svg" "$UNIT_DIR/syncjob@.service"
    # enabled instances leave their wants/ symlinks behind otherwise
    rm -f "$UNIT_DIR"/default.target.wants/syncjob@*.service
    sysd daemon-reload
    refresh_desktop

    # Only on --purge. A JOBS_DIR relocated outside $CONF_DIR (a shared
    # Nextcloud folder, say) is never touched: other machines read it.
    if [[ "${KIWI_PURGE:-0}" == 1 || "${1:-}" == --purge ]]; then
        say "purging $CONF_DIR (config + job definitions)"
        rm -rf "${CONF_DIR:?}"
    else
        say "kept: $CONF_DIR (config + job definitions) — remove with: $0 uninstall --purge"
    fi
}

case "$ACTION" in
    install)   do_install ;;
    update)    do_update ;;
    uninstall) shift || true; do_uninstall "${1:-}" ;;
    *) echo "usage: $0 install|update|uninstall [--purge]" >&2; exit 1 ;;
esac
