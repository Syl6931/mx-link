# MX Link

**MX Link is a local iPhone ↔ KDE Plasma bridge for text, links, photos, PDFs and files.**

It is designed to feel closer to Handoff/AirDrop while staying local: no cloud storage account, no VPN and no Internet-facing port.

[![MX Link overview](mx-link-overview.png)](mx-link-overview.png)

> **Version:** `0.1.2-alpha`
> **Status:** public alpha — functional, but still intended for testing.

## Supported setup

This alpha currently targets:

- KDE Plasma
- MX Linux / Debian-based distributions
- iPhone with Apple Shortcuts
- both devices on the same local network

Other distributions may work, but the installer currently uses Debian package names and `dpkg`.

## What MX Link does

### iPhone → Linux

From the iOS share sheet, run **MX Link** to send:

- text → copied to the KDE clipboard
- a URL → opened in the default browser
- one or more photos → saved locally, optionally opened
- a PDF → saved locally, optionally opened
- another file → saved locally

### Linux → iPhone

On Linux, copy text or one or more files in KDE, then run the **MX Link** Shortcut on the iPhone.

You can also **copy an image directly** from Chrome, a graphics app or a screenshot tool: MX Link detects Wayland clipboard bitmap data and transfers it as PNG, without changing the iOS Shortcut.

For files, the Shortcut offers **Save to Files** or **Share…**.


**Bitmap dependencies:** `wl-clipboard` (Wayland clipboard access) and `imagemagick` (non-PNG conversion) are installed by `install.sh` if needed. Temporary PNG files are kept under `~/.cache/mxlink/clipboard-bitmaps/` (private permissions) and removed by later requests after expiry. Files copied in Dolphin still work as before.

## Verify the bitmap fix

Run bitmap regression tests without touching your real clipboard:

```bash
python3 -m unittest discover -s tests -v
```

To rebuild and check distribution SHA-256 checksums (excluding `.git`):

```bash
python3 scripts/update_manifest.py
sha256sum -c MANIFEST.sha256
```

# Installation

## 1. Download

Download:

- `MX-Link-0.1.2-alpha.tar.gz`
- `MX-Link-0.1.2-alpha.tar.gz.sha256`

Optional but recommended:

```bash
sha256sum -c MX-Link-0.1.2-alpha.tar.gz.sha256
```

## 2. Extract

```bash
tar -xzf MX-Link-0.1.2-alpha.tar.gz
cd MX-Link-0.1.2-alpha
```

## 3. Check the package

```bash
bash install.sh --check
```

This does not install anything.

## 4. Install

```bash
bash install.sh
```

The installer sets up the daemon, local HTTP gateway, Plasma applet, pairing page, firewall rule, `.local` name resolution and Plasma session hook.

## 5. Pair the iPhone

Find the Linux hostname:

```bash
hostname -s
```

On the iPhone, connected to the same Wi‑Fi/LAN, open:

```text
http://HOSTNAME.local:8767/setup
```

Then:

1. **Install MX Link** — installs the official Shortcut from iCloud.
2. **Pair this iPhone** — sends the local connection settings to the Shortcut.

No TLS certificate or iOS configuration profile is required.

# Everyday use

## iPhone → Linux

Use the iOS share sheet and run **MX Link**.

Received files are stored by default under your Downloads folder in `MX Link`, for example:

```text
~/Downloads/MX Link
```

or a localized equivalent such as:

```text
~/Téléchargements/MX Link
```

## Linux → iPhone

Copy text or one or more files in KDE, then run the **MX Link** Shortcut on the iPhone.

# Plasma applet

The applet shows status, latest transfer, direction, recent filenames, pairing information and settings.

In **Settings → Receive** you can configure:

- automatic photo opening
- automatic PDF opening
- notifications
- receive folder
- photo application
- PDF application

By default MX Link follows the system file associations, for example:

```text
Photos: Default — qimgv
PDF:    Default — Okular
```

qimgv and Okular are **not dependencies**. They are only examples of current system defaults.

You can explicitly choose another compatible installed application. If that application disappears, MX Link falls back to the system default.

# Optional: iPhone Control Center

You can add the **MX Link** Shortcut to iOS Control Center for faster access.

# Network and privacy

The backend daemon listens only on:

```text
127.0.0.1:8765
```

The LAN gateway uses port:

```text
8767
```

and requires the pairing token.

MX Link does not require cloud storage, a VPN, an Internet-facing port, a TLS certificate or an iOS configuration profile.

The iCloud link is used to install the Shortcut. Normal transfers happen locally.

# After a reboot

MX Link runs as a user service and should start automatically. A Plasma session hook refreshes the graphical environment so received files can still be opened by desktop applications after login.

# Diagnostics

```bash
systemctl --user status mxlink.service
systemctl --user status mxlink-http.service
tail -n 80 ~/.local/state/mxlink/mxlink.log
```

# Uninstall

Keep configuration and pairing token:

```bash
bash uninstall.sh
```

Remove MX Link and configuration/token:

```bash
bash uninstall.sh --purge
```

Received files are not deleted.

# Alpha testing

Useful feedback includes installation, pairing, transfer reliability, behavior after reboot, different KDE file associations and unclear instructions.

When reporting a problem, please include Linux distribution/version, KDE Plasma version, iOS version, what you were sending, the exact failing step and relevant diagnostic output.

Remove personal filenames or sensitive information before posting logs publicly.

## French documentation

See **[README.fr.md](README.fr.md)**.
