#!/usr/bin/env bash
systemctl --user import-environment \
  DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE \
  XDG_CURRENT_DESKTOP DBUS_SESSION_BUS_ADDRESS 2>/dev/null || true

if command -v dbus-update-activation-environment >/dev/null 2>&1; then
  dbus-update-activation-environment --systemd \
    DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE \
    XDG_CURRENT_DESKTOP DBUS_SESSION_BUS_ADDRESS 2>/dev/null || true
fi

systemctl --user try-restart mxlink.service 2>/dev/null || true
