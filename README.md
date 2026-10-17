# MX Link — 0.1.4-alpha

Transfer text, links, images and files between iPhone and Linux on your local network.
Plasma 6 includes a panel widget. The engine also runs on other Wayland/X11 desktops or
without a desktop using a CLI. **Alpha release:** test pairing and transfers before relying on it.

## Install

Extract the release archive, enter its directory, then run as your normal user:

```bash
bash install.sh --check
bash install.sh
```

Supported automatic installer: MX Linux/Debian, Python 3.11+, a **systemd user manager**.
Plasma is optional and detected automatically. For a server use `bash install.sh --headless`;
this forces headless exchange even if a display environment exists, without installing GUI dependencies.
Other distributions require manual dependencies and `--skip-deps`; they are not release-tested.
Wayland clipboard capabilities depend on compositor protocol support.

The installer uses sudo for dependencies, Avahi and UFW. It does not run as root itself.
For unattended startup without login, an administrator may explicitly enable lingering with
`sudo loginctl enable-linger "$USER"`. Systems without a systemd user manager need another
service integration and are not supported by this installer.

## Pair

Use the widget's **Appairer un iPhone**, or `~/.local/bin/mxlink pair`.
Open its private link/QR on iPhone, install the **MX Link** Shortcut, return to the page,
choose **Appairer cet iPhone** directly on that same page.
The grant expires after five minutes and is consumed when tapping the pairing button. Generate a
new link if it expires; creating one invalidates the previous link. `/setup` alone reveals no token.

The existing Shortcut remains compatible. iCloud distributes it and may synchronize
`Shortcuts/MXLink-config.json`, which contains the shared computer token. **Transfers themselves
are direct LAN transfers**, not cloud storage. No background iOS app or automatic clipboard sync.

## Use

Share from iPhone with **Share → MX Link**. To retrieve Linux content, copy text, images or
files on Linux and run **MX Link → Récupérer depuis MX** on iPhone. **Envoyer vers MX** sends
iPhone clipboard text. Received files go to Downloads/MX Link. Desktop URLs use the default browser.
In headless mode, files are saved and text/URLs are retained in private exchange state:

```bash
printf 'Hello' | ~/.local/bin/mxlink set-text
~/.local/bin/mxlink get-text
~/.local/bin/mxlink send-files /path/to/file.pdf
~/.local/bin/mxlink status
~/.local/bin/mxlink config
printf '{"open_images":false}' | ~/.local/bin/mxlink set-config
```

`send-files` is headless-only. Desktop sessions use their file manager clipboard.
Current headless text persists until replaced or purged, outside logs/history.

## Network and security

LAN gateway: **TCP 8767**, all IPv4 interfaces. Local engine: **127.0.0.1:8765**.
The installer adds a UFW rule for the detected local subnet, but **does not enable UFW**.
Configure other firewalls yourself. mDNS/Avahi resolves the computer's `.local` name.
**No router port forwarding or DMZ is required. Do not expose these ports to the Internet.**

**HTTP is unencrypted: trusted LAN only.** Temporary pairing does not prevent interception.
The gateway allowlist blocks local configuration, history and administration APIs.
All paired phones currently share one computer token. See [SECURITY.md](SECURITY.md).

## Remove / validate

```bash
bash uninstall.sh           # keep pairing/configuration
bash uninstall.sh --purge   # also remove token, state, logs and cache
python3 -m unittest discover -s tests -v
sha256sum -c MANIFEST.sha256
```

Received files and old backups are retained. Tests use isolated homes, fake OS commands for
installer lifecycle, and real HTTP services on 8765/8767 for integration tests (skipped if occupied).
A CI workflow is included to run the test suite on GitHub.
[French clean-install test guide](docs/TEST-CANDIDAT.fr.md) · [Audit mapping](docs/AUDIT-0.1.4.md).
