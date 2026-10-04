#!/bin/bash

QDBUS="$(command -v qdbus6 || command -v qdbus)" || exit 1
SCRIPT="$HOME/.local/share/mxlink/maximize-next-gwenview.js"
NAME="mxlink-maximize-next-gwenview"

"$QDBUS" org.kde.KWin /Scripting \
    org.kde.kwin.Scripting.unloadScript "$NAME" \
    >/dev/null 2>&1 || true

ID=$(
    "$QDBUS" org.kde.KWin /Scripting \
        org.kde.kwin.Scripting.loadScript "$SCRIPT" "$NAME"
)

[ -n "$ID" ] || exit 1

"$QDBUS" org.kde.KWin "/Scripting/Script$ID" \
    org.kde.kwin.Script.run \
    >/dev/null 2>&1

(
    sleep 5

    "$QDBUS" org.kde.KWin "/Scripting/Script$ID" \
        org.kde.kwin.Script.stop \
        >/dev/null 2>&1 || true

    "$QDBUS" org.kde.KWin /Scripting \
        org.kde.kwin.Scripting.unloadScript "$NAME" \
        >/dev/null 2>&1 || true
) &

exit 0
