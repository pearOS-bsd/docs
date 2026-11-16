# Goal: our Dock is indistinguishable from the real one, and can replace it on a real Mac

Decision of the user (2026-11-16). Two requirements:
1. **Indistinguishable under trace.** The same Mach services looked up and provided, the same files opened, the same preference keys read and written, the same distributed notifications, the same SkyLight requests, in the same order where order matters. A trace of ours and of the real Dock differ only in timing and ids.
2. **Runs on a real macOS.** On the Mac VM we stop `com.apple.Dock.agent`, start ours in its place, and the rest of the system (SystemUIServer, Finder, Spotlight, System Settings ...) does not notice.

## Consequences for the design
- `apps/dock` (today: GNUstep + Opal + our `ws_*` window API, 883 lines) cannot run on macOS. The new Dock is **one Objective-C source on the Cocoa API**: on macOS it links the real AppKit, on pearOS our `open` AppKit. SkyLight, CoreServices, QuartzCore, CFPreferences are called the way Apple's Dock calls them. The current Dock stays until the new one passes the trace comparison.
- It **provides** the Mach services of the real Dock (from its launchd plist on the Mac): `com.apple.dock.server`, `.spaces`, `.fullscreen`, `.launchpad`, `.notificationcenter`, `.ppt`, `.spotlight`, `.sidecar`, `.appstore`, `.downloads`, `.remotedesktoppicture`, `com.apple.desktoppicture.cache-delete` (all with `HideUntilCheckIn`). The agent plist (ours, same labels and service names; `KeepAlive` after initial demand and not after a successful exit, `POSIXSpawnType = App`, `ThrottleInterval 1`) is written by us, not copied.
- It **looks up** the services listed in `DOCK-SERVICES.md` and reads/writes `com.apple.dock` through cfprefsd (`CFPreferences`), not the file.

## Facts about the Mac VM (read 2026-11-16)
| fact | value |
|---|---|
| macOS | 26.7.2, x86_64 |
| SIP | **disabled**; authenticated root **enabled** (the sealed system volume stays read-only: we never modify `/System`, we replace the *job*) |
| boot-args | `keepsyms=1` only (AMFI is active) |
| Dock signature | `flags=0x0 (none)`: no hardened runtime, no team id; **many private entitlements** (`com.apple.private.SkyLight.displaycontrol`, `...screencapturedirect`, `...user-accessibility-report`, `coreservices.canaccessanysharedfilelist`, `dmd.policy`, `backgroundtaskmanagement.manage`, `aps-connection-initiate`, `chrono.controls`, ...) |
| the job | `gui/501/com.apple.Dock.agent`, plist `/System/Library/LaunchAgents/com.apple.Dock.plist` |
| tools without root | `lsof`, `launchctl print`, `codesign`, `log`, `clang`, `python3`; **not** `dtrace` / `fs_usage` (they need root; `sudo` asks for a password) |

## Method
**Trace without root:** an interposer dylib (`__DATA,__interpose`, built with clang on the Mac) logs `bootstrap_look_up`, `bootstrap_check_in`, `xpc_connection_create_mach_service`, `open`/`stat` on paths, `CFPreferences*`, `notify_*`, `CFNotificationCenter` (distributed), `SLS*` calls. It is loaded with `DYLD_INSERT_LIBRARIES` through a copy of the agent plist (`EnvironmentVariables`) that we `launchctl bootstrap` into `gui/501` after `launchctl bootout` of the original. The Dock has no hardened runtime, so with SIP off this should be accepted: **not tried yet**.
**Compare:** the same interposer runs in ours; a script diffs the two logs (names and arguments, ids masked). The real Dock's log is the golden file (kept in `research/`, sanitised of the user's data).
**Replace:** the same plist mechanism with our binary.

## Blockers that need the user
- **Root on the Mac VM** (the `alex` password, or a `NOPASSWD` sudoers line): for `dtrace`/`fs_usage` (a complete trace including paths the interposer misses) and for the boot-arg below.
- **AMFI:** our binary will carry the same private entitlements to be served by SkyLight, SystemUIServer and others; AMFI kills an ad-hoc signed binary with restricted entitlements. Likely needed on the Mac VM: `nvram boot-args="keepsyms=1 amfi_get_out_of_my_way=1"` and a reboot (root). Until then ours runs with the public API only and the private requests are refused: that is already a visible difference.

## Order
1. Capture the real Dock's trace with the interposer (golden). 2. Write the trace comparator. 3. New Dock skeleton on Cocoa: prefs through `CFPreferences`, the same tile model, the services answering minimally (tile size, magnification, orientation, hide, bounce). 4. Run it on the Mac VM in place of the real one, diff the traces, repeat. 5. The same source on pearOS (`open` AppKit + the stack of `d/`). 6. Look: pixel comparison against the real Dock on the same display.
