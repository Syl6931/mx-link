#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    echo "Utilisez : bash uninstall.sh"
    return 1 2>/dev/null || exit 1
fi

set -Eeuo pipefail

PURGE="${1:-}"

APP_DIR="$HOME/.local/share/mxlink"
CONFIG_DIR="$HOME/.config/mxlink"
SYSTEMD_DIR="$HOME/.config/systemd/user"
PLASMOID_ID="org.mxlink.plasmoid"
PLASMOID_DIR="$HOME/.local/share/plasma/plasmoids/$PLASMOID_ID"

echo "=== Désinstallation MX Link ==="

QDBUS="$(command -v qdbus6 || command -v qdbus || true)"

if [ -n "$QDBUS" ]; then
    "$QDBUS" \
        org.kde.plasmashell \
        /PlasmaShell \
        org.kde.PlasmaShell.evaluateScript \
'var plugin = "org.mxlink.plasmoid";
var ps = panels();

for (var i = 0; i < ps.length; ++i) {
    var ws = ps[i].widgets();

    for (var j = ws.length - 1; j >= 0; --j) {
        if (ws[j].type === plugin)
            ws[j].remove();
    }
}' >/dev/null 2>&1 || true
fi

systemctl --user disable --now \
    mxlink-http.service \
    mxlink.service \
    2>/dev/null || true

rm -f \
    "$SYSTEMD_DIR/mxlink.service" \
    "$SYSTEMD_DIR/mxlink-http.service"

systemctl --user daemon-reload

NETWORK=""

if [ -f "$CONFIG_DIR/install.env" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_DIR/install.env"
    NETWORK="${MXLINK_NETWORK:-}"
fi

if [ -n "$NETWORK" ] && command -v ufw >/dev/null 2>&1; then
    sudo ufw delete allow \
        from "$NETWORK" \
        to any port 8767 \
        proto tcp \
        >/dev/null 2>&1 || true
fi

if command -v kpackagetool6 >/dev/null 2>&1; then
    kpackagetool6 \
        --type Plasma/Applet \
        --remove "$PLASMOID_ID" \
        >/dev/null 2>&1 || true
fi

rm -rf "$PLASMOID_DIR" "$APP_DIR"

if [ "$PURGE" = "--purge" ]; then
    rm -rf "$CONFIG_DIR"
    echo "✓ configuration et jeton supprimés"
else
    echo "• configuration conservée dans $CONFIG_DIR"
fi

echo "✓ MX Link désinstallé"
echo "Les fichiers reçus dans Téléchargements/MX Link sont conservés."
