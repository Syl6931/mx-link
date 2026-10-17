# Audit consolidation — candidate 1

Base: GitHub `1ebdf7ea72a7c43c89c15298d3f744144237bb1d` (0.1.3-alpha).
Installed engine and widget were compared with GitHub before edits. The only engine
mismatch was the older bitmap module lacking two explicit permission restrictions;
the stronger repository version was retained. No unpublished widget changes were found.

| Finding / scope | Candidate implementation | Evidence |
| --- | --- | --- |
| Public setup discloses token | Private expiring grant, atomic one-use POST redemption, no-store | Integration pairing tests |
| LAN access to config / local actions | Explicit method/path allowlist | Integration route tests |
| Fresh HOME fails before logging directory exists | Create private state directory before rotating logger | Fresh-process integration |
| Incorrect escaped magic bytes | Real JPEG/PNG/ZIP signatures | Upload integration |
| Filename header lost in gateway | Forward X-MX-Filename and retain query fallback | Upload integration |
| Sensitive logs | Remove clipboard excerpts, URL payloads and full config logging; rotation | Text privacy integration |
| Upload memory / malformed length | Streaming private files, length limits, incomplete cleanup, worker cap/timeouts | HTTP integration |
| Filename collision / permissions | Exclusive atomic hardlink publication, private umask | Upload collision tests |
| Unbounded snapshots | 32 sessions, TTL, 100 files per snapshot | Code limits; manual large selections still useful |
| Obsolete code | Remove certificate endpoint, log-parsed status, Chrome-specific helper, old in-memory upload helper | Source diff |
| Maintainability | Separate clipboard adapters, HTTP limits, pairing, CLI; retain proven history/bitmap modules | Module structure and regression suite |
| Plasma coupling | Optional widget; X11/Wayland adapters; forced headless mode; generic autostart | Adapter tests, headless integration, installer simulation |
| Installer / uninstall | Manifest validation, restart on upgrade, private defaults, no required Plasma tools; purge state/cache | Installer lifecycle test |
| Documentation / CI | Bilingual README, security model, reset/acceptance guide, automated workflow | Included files |

Known limits: HTTP confidentiality, shared device token, trusted local user assumption,
systemd user manager required, no universal compositor guarantee. No iPhone or live KDE
acceptance result is claimed. The candidate leaves the current installed version unchanged.
