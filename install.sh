#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    echo "Ne sourcez pas ce script. Utilisez : bash install.sh"
    return 1 2>/dev/null || exit 1
fi

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VERSION="$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo inconnue)"

SRC_DIR="$SCRIPT_DIR/src"
PLASMOID_SRC="$SCRIPT_DIR/plasmoid"

APP_DIR="$HOME/.local/share/mxlink"
CONFIG_DIR="$HOME/.config/mxlink"
SYSTEMD_DIR="$HOME/.config/systemd/user"
PLASMOID_ID="org.mxlink.plasmoid"
PLASMOID_DIR="$HOME/.local/share/plasma/plasmoids/$PLASMOID_ID"
BACKUP_BASE="$HOME/.local/share/mxlink-backups"

MODE="${1:---install}"

say() { printf '%s\n' "$*"; }
die() { say "ERREUR : $*"; exit 1; }

check_payload() {
    say
    say "=== Vérification du paquet ==="

    for f in \
        "$SRC_DIR/mxlink.py" \
        "$SRC_DIR/mxlink-http-gateway.py" \
        "$PLASMOID_SRC/metadata.json" \
        "$PLASMOID_SRC/contents/ui/main.qml"
    do
        [ -f "$f" ] || die "fichier absent : $f"
    done

    python3 -m py_compile \
        "$SRC_DIR/mxlink.py" \
        "$SRC_DIR/mxlink-http-gateway.py"
    say "✓ syntaxe Python"

    python3 - "$PLASMOID_SRC/metadata.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    json.load(f)
PY
    say "✓ metadata.json"

    grep -q '4550a09c4c964894a4679a28455b921d' \
        "$SRC_DIR/mxlink-http-gateway.py" \
        || die "lien du raccourci iCloud maître absent"
    say "✓ raccourci iCloud maître"

    grep -q 'Appairer un iPhone' \
        "$PLASMOID_SRC/contents/ui/main.qml" \
        || die "interface d'appairage absente"
    say "✓ interface d'appairage"
}

check_environment() {
    say
    say "=== Environnement ==="

    for cmd in python3 systemctl ip curl; do
        command -v "$cmd" >/dev/null 2>&1 \
            && say "✓ $cmd" \
            || say "✗ $cmd absent"
    done

    command -v plasmashell >/dev/null 2>&1 \
        && say "✓ Plasma : $(plasmashell --version 2>/dev/null || echo présent)" \
        || say "⚠ Plasma non détecté"

    command -v kpackagetool6 >/dev/null 2>&1 \
        && say "✓ kpackagetool6" \
        || say "✗ kpackagetool6 absent"

    command -v qrencode >/dev/null 2>&1 \
        && say "✓ qrencode" \
        || say "• qrencode sera installé"

    say "✓ nom mDNS prévu : $(hostname -s).local"
}

if [ "$MODE" = "--check" ]; then
    say "MX Link $VERSION — contrôle du paquet"
    check_payload
    check_environment

    say
    say "✓ CHECK TERMINÉ — aucune modification effectuée"
    exit 0
fi

[ "$MODE" = "--install" ] \
    || die "Usage : bash install.sh --check | --install"

say "======================================================"
say " MX Link $VERSION — installation"
say "======================================================"

check_payload

say
say "=== Dépendances ==="

PACKAGES=(
    python3
    curl
    qrencode
    xdg-user-dirs
    libnotify-bin

    avahi-daemon
    libnss-mdns
    ufw
)

MISSING=()

command -v dpkg >/dev/null 2>&1 \
    || die "Cette version cible Debian/MX Linux."

for pkg in "${PACKAGES[@]}"; do
    dpkg -s "$pkg" >/dev/null 2>&1 || MISSING+=("$pkg")
done

if [ "${#MISSING[@]}" -gt 0 ]; then
    say "Installation : ${MISSING[*]}"
    sudo apt-get update
    sudo apt-get install -y "${MISSING[@]}"
else
    say "✓ dépendances déjà présentes"
fi

command -v kpackagetool6 >/dev/null 2>&1 \
    || die "kpackagetool6 est requis pour installer l'applet Plasma"

sudo systemctl enable --now avahi-daemon >/dev/null 2>&1 || true

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$BACKUP_BASE/$STAMP"

if [ -d "$APP_DIR" ] || [ -d "$PLASMOID_DIR" ]; then
    mkdir -p "$BACKUP"
    [ ! -d "$APP_DIR" ] || cp -a "$APP_DIR" "$BACKUP/mxlink"
    [ ! -d "$PLASMOID_DIR" ] || cp -a "$PLASMOID_DIR" "$BACKUP/plasmoid"
    say "✓ sauvegarde : $BACKUP"
fi

say
say "=== Fichiers MX Link ==="

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

cp -a "$SRC_DIR/." "$APP_DIR/"

chmod 700 \
    "$APP_DIR/mxlink.py" \
    "$APP_DIR/mxlink-http-gateway.py"

say "✓ daemon et gateway"

[ ! -f "$APP_DIR/mxlink-session-environment.sh" ] || chmod 700 "$APP_DIR/mxlink-session-environment.sh"

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/mxlink-session-environment.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=MX Link session environment
Comment=Expose la session graphique Plasma aux services MX Link
Exec=$APP_DIR/mxlink-session-environment.sh
OnlyShowIn=KDE;
X-KDE-autostart-after=panel
NoDisplay=true
EOF

mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cat > "$CONFIG_DIR/config.json" <<'JSON'
{
  "receive_dir": "",
  "open_images": true,
  "image_opener": "default",
  "open_pdfs": true,
  "pdf_opener": "default",
  "notifications": true
}
JSON
    say "✓ configuration créée"
else
    say "✓ configuration existante conservée"
fi

if [ ! -s "$CONFIG_DIR/token" ]; then
    python3 - <<'PY'
from pathlib import Path
import secrets

p = Path.home() / ".config/mxlink/token"
p.write_text(secrets.token_urlsafe(32), encoding="utf-8")
p.chmod(0o600)
PY
    say "✓ nouveau jeton généré"
else
    chmod 600 "$CONFIG_DIR/token"
    say "✓ jeton existant conservé"
fi

say
say "=== Applet Plasma ==="

if [ -d "$PLASMOID_DIR" ]; then
    kpackagetool6 \
        --type Plasma/Applet \
        --upgrade "$PLASMOID_SRC" \
        >/dev/null 2>&1 \
    || true
else
    kpackagetool6 \
        --type Plasma/Applet \
        --install "$PLASMOID_SRC" \
        >/dev/null
fi

[ -d "$PLASMOID_DIR" ] \
    || die "l'installation du plasmoid a échoué"

HOST_SHORT="$(hostname -s)"
MDNS_HOST="${HOST_SHORT}.local"
SETUP_URL="http://${MDNS_HOST}:8767/setup"

QML="$PLASMOID_DIR/contents/ui/main.qml"
QR="$PLASMOID_DIR/contents/images/pairing-qr.png"

mkdir -p "$(dirname "$QR")"

python3 - "$QML" "$SETUP_URL" <<'PY'
from pathlib import Path
import re
import sys

p = Path(sys.argv[1])
url = sys.argv[2]
s = p.read_text(encoding="utf-8")

s, n = re.subn(
    r'property string pairingUrl:\s*"[^"]*"',
    f'property string pairingUrl: "{url}"',
    s,
    count=1
)
if n != 1:
    raise SystemExit("pairingUrl introuvable dans le QML installé")

p.write_text(s, encoding="utf-8")
PY

qrencode -o "$QR" -s 12 -m 3 "$SETUP_URL"
say "✓ QR généré : $SETUP_URL"

say
say "=== Services ==="

mkdir -p "$SYSTEMD_DIR"

cat > "$SYSTEMD_DIR/mxlink.service" <<'UNIT'
[Unit]
Description=MX Link daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.local/share/mxlink/mxlink.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
UNIT

cat > "$SYSTEMD_DIR/mxlink-http.service" <<'UNIT'
[Unit]
Description=MX Link HTTP gateway
After=network-online.target mxlink.service
Wants=mxlink.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.local/share/mxlink/mxlink-http-gateway.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
UNIT

systemctl --user import-environment \
    DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE \
    XDG_CURRENT_DESKTOP DBUS_SESSION_BUS_ADDRESS \
    2>/dev/null || true

if command -v dbus-update-activation-environment >/dev/null 2>&1; then
    dbus-update-activation-environment \
        --systemd \
        DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE \
        XDG_CURRENT_DESKTOP DBUS_SESSION_BUS_ADDRESS \
        2>/dev/null || true
fi

systemctl --user daemon-reload
systemctl --user enable --now mxlink.service mxlink-http.service

say "✓ services démarrés"

say
say "=== Pare-feu ==="

IFACE="$(ip route show default | awk 'NR==1 {print $5}')"
CIDR="$(
    ip -o -4 addr show dev "$IFACE" scope global \
    | awk 'NR==1 {print $4}'
)"

[ -n "$CIDR" ] || die "Impossible d'identifier le réseau local"

NETWORK="$(
    python3 - "$CIDR" <<'PY'
import ipaddress
import sys
print(ipaddress.ip_network(sys.argv[1], strict=False))
PY
)"

cat > "$CONFIG_DIR/install.env" <<EOF
MXLINK_INTERFACE=$IFACE
MXLINK_NETWORK=$NETWORK
MXLINK_MDNS_HOST=$MDNS_HOST
EOF

if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow \
        from "$NETWORK" \
        to any port 8767 \
        proto tcp \
        comment 'MX Link HTTP' \
        >/dev/null

    sudo ufw status | grep -q '^Status: active' \
        && say "✓ UFW : 8767 autorisé depuis $NETWORK" \
        || say "⚠ règle UFW ajoutée mais UFW n'est pas actif"
fi

say
say "=== Ajout de l'applet au panneau ==="

QDBUS="$(command -v qdbus6 || command -v qdbus || true)"

if [ -n "$QDBUS" ]; then
    "$QDBUS" \
        org.kde.plasmashell \
        /PlasmaShell \
        org.kde.PlasmaShell.evaluateScript \
'var plugin = "org.mxlink.plasmoid";
var ps = panels();
var target = null;

for (var i = 0; i < ps.length; ++i) {
    if (ps[i].location === "top") {
        target = ps[i];
        break;
    }
}

if (target === null && ps.length > 0)
    target = ps[0];

if (target !== null) {
    for (var i = 0; i < ps.length; ++i) {
        var ws = ps[i].widgets();

        for (var j = ws.length - 1; j >= 0; --j) {
            if (ws[j].type === plugin && ps[i].id !== target.id)
                ws[j].remove();
        }
    }

    var found = false;
    var targetWidgets = target.widgets();

    for (var j = 0; j < targetWidgets.length; ++j) {
        if (targetWidgets[j].type === plugin)
            found = true;
    }

    if (!found)
        target.addWidget(plugin);
}' >/dev/null 2>&1 || true

    say "✓ applet traitée"
else
    say "⚠ qdbus indisponible : ajoutez MX Link manuellement au panneau"
fi

say
say "=== Tests ==="

sleep 1

systemctl --user is-active --quiet mxlink.service \
    || die "mxlink.service inactif"

systemctl --user is-active --quiet mxlink-http.service \
    || die "mxlink-http.service inactif"

TOKEN="$(cat "$CONFIG_DIR/token")"

RESULT="$(
    curl -fsS "http://127.0.0.1:8767/health?key=$TOKEN"
)"

[ "$RESULT" = "MX Link OK" ] \
    || die "/health inattendu : $RESULT"

curl -fsS "http://127.0.0.1:8767/setup" >/dev/null

say "✓ daemon"
say "✓ gateway"
say "✓ page d'appairage"

if curl -fsS --max-time 4 \
    "http://${MDNS_HOST}:8767/setup" \
    >/dev/null 2>&1
then
    say "✓ mDNS : $MDNS_HOST"
else
    say "⚠ $MDNS_HOST n'est pas encore résolu"
fi

say
say "======================================================"
say " MX LINK INSTALLÉ"
say "======================================================"
say
say "Page d'appairage : $SETUP_URL"
say "Aucun certificat HTTPS n'est nécessaire."
