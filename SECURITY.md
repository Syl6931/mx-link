# Security model — 0.1.4-alpha candidate

MX Link is intended for a trusted local network and a trusted Linux user account.
It is not an Internet-facing service. Do not forward its ports or enable a router DMZ.

- LAN HTTP gateway on all IPv4 interfaces, TCP 8767. Bearer authentication, with legacy
  `key`/`token` query parameters retained for the published Apple Shortcut. Query credentials
  are stripped before forwarding; HTTP access logging is disabled. Do not share request URLs.
- Local HTTP engine on 127.0.0.1:8765. It trusts local applications running on the machine;
  **it does not isolate users on an untrusted multi-user host**. Host validation and rejection
  of browser origins reduce DNS-rebinding/CSRF exposure. Local administration POSTs require JSON.
- Explicit allowlist of transfer endpoints on the LAN gateway. Configuration, history and
  pairing-window creation never forward from LAN to the local engine.
- Pairing grants: 256-bit random capability, five-minute lifetime, one redemption under
  an interprocess lock. GET allows installing the Shortcut without exposing the permanent token;
  POST consumes the grant before rendering the Shortcut pairing link. A new grant replaces the old.
- All paired phones share one persistent token. Revoke all pairings with uninstall `--purge`
  and reinstall, then pair trusted devices again. Per-device revocation is not implemented.
- HTTP is **not encrypted**. A network observer can capture a grant, token or transferred data.
  A stolen token authorizes clipboard reads, file uploads and supported URL/text actions.
  This candidate does not claim TLS, mutual authentication or protection on hostile Wi-Fi.
- iCloud hosts the Shortcut and can synchronize `Shortcuts/MXLink-config.json` including the
  token. Payload transfers are local. The configuration is not a public share link.
- At most eight worker connections per service; 30-second socket inactivity timeout;
  500 MiB upload limit; 1 MiB JSON/text limit; streamed uploads and downloads; up to 32
  clipboard snapshots, 100 files per snapshot, 15-minute expiry. Bitmap capture has separate
  size/conversion limits and subprocess timeouts. This is not protection against sustained DoS
  or exhaustion of disk space by an authenticated user.
- Private temporary upload files, atomic collision-safe publication, restrictive umask and
  token/cache permissions. Transfers are not malware-scanned; inspect untrusted files.
- Logs rotate at 1 MiB with two backups. Clipboard text and URL payloads are not logged.
  Local history intentionally retains recent filenames/URLs and is purgeable. Headless mode
  intentionally persists current text/file selection with mode 0600 until replaced or purged.

Report security issues privately to the repository maintainer; do not attach tokens, pairing
URLs, personal transfer histories or raw configuration files to public issues.
