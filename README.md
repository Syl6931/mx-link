# MX Link

**Share photos, files, text and links between iPhone and KDE Plasma — over your local network.**

**One iOS Shortcut. Both ways. No background app. No cloud.**

[![MX Link overview](mx-link-overview.png)](mx-link-overview.png)

## What it does

**iPhone → KDE**
- Share photos, PDFs or files from the iOS share sheet. They're saved on KDE; photos and PDFs can open automatically.
- Share a URL to open it directly in your desktop browser.
- Share text to copy it to the KDE clipboard.

**KDE → iPhone**
- Copy text, an image or files on KDE.
- Run the **MX Link** Shortcut on iPhone and select **Get from MX**.

**iPhone clipboard → KDE**
- Run the same Shortcut and select **Send to MX** to send clipboard text.

**Every transfer is initiated from the iPhone.** Nothing runs in the background on iOS, and clipboard syncing is not automatic.

## Get started

You'll need KDE Plasma on MX Linux or a Debian-based distribution, an iPhone with Apple Shortcuts, and both devices on the same local network.

Install MX Link on KDE:

```bash
git clone https://github.com/Syl6931/mx-link.git
cd mx-link
bash install.sh
```

Open the **MX Link** widget in the Plasma panel and select **Pair an iPhone**. Scan its QR code, install the iOS Shortcut, then tap **Pair this iPhone** on the setup page.

That's it. On iPhone, use **Share → MX Link** to send something immediately, or launch the **MX Link** Shortcut on its own to choose a clipboard direction.

Received files go to **Downloads/MX Link** by default. The Plasma widget shows recent transfers and reception settings.

## Local network access and security

MX Link needs **inbound TCP port 8767 on your Linux computer** so the iPhone can reach it. The gateway listens on all network interfaces (`0.0.0.0:8767`); its internal daemon listens only on `127.0.0.1:8765`. No router port forwarding or Internet-facing port is needed — **do not forward TCP 8767 on your router**.

During installation, MX Link adds a UFW firewall allow rule for TCP 8767 **from the local IPv4 subnet detected on the default network interface**. The installer does **not** enable UFW. The rule restricts access only when UFW is active; if you use another firewall, configure it yourself. On machines with multiple network interfaces, check which networks can reach port 8767.

**Use MX Link only on a trusted local network.** The `/setup` pairing page can be opened without authentication and includes the pairing token: anyone who can reach that page can obtain the token. Other transfer requests require that token, but traffic uses **unencrypted HTTP**, not HTTPS. Avoid public or untrusted Wi-Fi.

## Uninstall

```bash
bash uninstall.sh
```

To remove pairing settings as well, use `bash uninstall.sh --purge`. Previously received files are kept.

[Lire en français](README.fr.md).
