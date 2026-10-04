# MX Link

**English | [Français](README.fr.md)**

MX Link is a local bridge between **KDE Plasma** and **iPhone** for quickly exchanging clipboard content and files in both directions.

> **Status:** `0.1.0-alpha` — early public testing release.

## Features

- Text and URLs from iPhone → PC
- Text and URLs from PC → iPhone
- One or multiple files from iPhone → PC
- One or multiple files from PC → iPhone
- Direct streaming for file batches, without creating an intermediate ZIP archive
- Automatic opening of received images in Gwenview
- Automatic opening of received PDFs with the default application
- Plasma applet showing availability and the latest transfer activity
- Transfer direction, file count, total size and file names in the applet
- iPhone pairing through a QR code
- Local discovery through mDNS (`hostname.local`)
- No HTTPS certificate to install on iOS

## Target platform

This first alpha targets:

- MX Linux / Debian-based systems
- KDE Plasma 6
- iPhone / iOS with Apple Shortcuts
- Both devices connected to the same trusted local network

Other Linux distributions may work later, but are not yet supported by the installer.

## Installation

Extract the release archive, then run:

```bash
bash install.sh --check
bash install.sh --install
```

The installer:

1. checks and installs required dependencies;
2. installs the local MX Link daemon;
3. installs the LAN HTTP gateway;
4. generates a random pairing token;
5. installs the Plasma applet;
6. adds MX Link to the top Plasma panel when available;
7. installs and enables user systemd services;
8. enables local mDNS discovery through Avahi;
9. restricts TCP port `8767` to the local network through UFW;
10. generates the machine-specific pairing QR code.

## Pair an iPhone

Open the **MX Link** Plasma applet and choose **Pair an iPhone**.

Then, on the iPhone:

1. scan the QR code;
2. tap **Install MX Link**;
3. add the Shortcut;
4. return to the setup page;
5. tap **Pair this iPhone**.

The shared iOS Shortcut does not contain a personal IP address or pairing token. Pairing stores the local machine configuration on the iPhone.

For faster daily access, you can add **MX Link** as a large Shortcut control in the iOS Control Center.

## Usage

### PC → iPhone

**Clipboard**

1. Copy text or a URL on KDE.
2. Run **MX Link** on the iPhone.
3. Paste normally on iOS.

**Files**

1. Select one or more files in Dolphin.
2. Copy them with `Ctrl+C`.
3. Run **MX Link** on the iPhone.
4. Choose **Save to Files** or **Share…**.

MX Link reads the current KDE clipboard only when the iPhone requests it. Copying or sorting files on the PC does not trigger background transfers.

### iPhone → PC

Use the iOS Share Sheet and choose **MX Link**.

Received files are stored by default in:

```text
~/Downloads/MX Link
```

The receive folder and automatic opening behavior can be changed in the Plasma applet.

## Architecture

MX Link uses two local services:

- `127.0.0.1:8765` — main daemon, local-only
- `0.0.0.0:8767` — LAN gateway, protected by the pairing token

The iPhone connects to the machine through its mDNS name, for example:

```text
http://mycomputer.local:8767
```

This avoids depending on a DHCP-assigned IP address.

## Security

MX Link is designed for a **trusted local network**.

The LAN gateway requires a randomly generated pairing token, but traffic between the iPhone and the PC uses plain HTTP and is **not encrypted**.

Do not use MX Link on an untrusted local network.

See [SECURITY.md](SECURITY.md) for details.

## Uninstall

```bash
bash uninstall.sh
```

To also delete configuration and the pairing token:

```bash
bash uninstall.sh --purge
```

Files previously received in `Downloads/MX Link` are preserved.

## Known alpha limitations

- Installer currently targets Debian / MX Linux.
- The iPhone side depends on Apple Shortcuts.
- HTTP transport assumes a trusted LAN.
- Multi-device and multi-PC pairing are still basic.
- Upgrade behavior will evolve before a stable release.

## License

MIT — see [LICENSE](LICENSE).
