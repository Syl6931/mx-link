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

## Uninstall

```bash
bash uninstall.sh
```

To remove pairing settings as well, use `bash uninstall.sh --purge`. Previously received files are kept.

[Lire en français](README.fr.md).
