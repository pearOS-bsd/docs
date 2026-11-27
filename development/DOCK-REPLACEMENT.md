# Goal: our Dock is indistinguishable from the real one, and can replace it on a real Mac

Decision of the user (2026-11-16). Two requirements:
1. **Indistinguishable under trace.** The same Mach services looked up and provided, the same files opened, the same preference keys read and written, the same distributed notifications, the same SkyLight requests, in the same order where order matters. A trace of ours and of the real Dock differ only in timing and ids.
2. **Runs on a real macOS.** On the Mac VM we stop `com.apple.Dock.agent`, start ours in its place, and the rest of the system (SystemUIServer, Finder, Spotlight, System Settings ...) does not notice.

## Consequences for the design
- `apps/dock` (GNUstep + Opal + our `ws_*` window API, 883 lines; removed 2026-11-27, apps 39009b2) could not run on macOS. The new Dock is **one Objective-C source on Foundation + QuartzCore + SkyLight + CoreUI + IconServices + CoreServices, WITHOUT AppKit**: `otool -L` of the real Dock (26.7.2) lists exactly these (plus SwiftUICore, Combine, RenderBox and many Swift libraries) and no AppKit. On macOS it links Apple's frameworks, on pearOS our `QuartzCore`, `SkyLight`, `CoreUI` repositories. (An earlier version of this page said "Cocoa/AppKit": wrong.) It is also a bundle (`Contents/Info.plist`, `LSUIElement`), like the real one. The current Dock stays until the new one passes the trace comparison.
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
**Trace (done, 2026-11-16): `research/dock-trace/capture.sh`, dtrace as root (`sudo` with `pear` works on the Mac VM; `fs_usage` does not start there).** The first golden trace is `research/dock-trace/real-dock-startup-macos26.7.2.txt`. What the real Dock does at startup:
- looks up: `com.apple.CARenderServer`, `CoreServices.coreservicesd`, `dock.server`, `fonts`, `logd`, `PowerManagement.control`, `system.notification_center`, `windowserver.active`;
- checks in: `com.apple.dock.server` and `EyeCandyDiagnose`;
- opens 28 XPC connections: analyticsd, appsleep, backgroundtaskmanagement, cfprefsd agent + daemon, coreservices appleevents / launchservicesd / lsbestappsuggestionmanager / sharedfilelistd, distributed_notifications, dmd.policy, dock.{fullscreen,notificationcenter,ppt,remotedesktoppicture,sidecar,spaces}, iconservices (+store), lsd.mapdb / modifydb, ProgressReporting, tccd.system, trustd.agent, uninstall.service, usernoted.dock, wallpaper, windowmanager.external;
- reads 40 preference keys with `CFPreferencesCopyAppValue`: tilesize, largesize, magnification, orientation, launchanim, mineffect(-immutable), minimize-to-application-immutable, min-in-place-immutable, position-immutable, static-only, static-apps, static-others, persistent-apps, persistent-others, recent-apps, version, loc, region, use-unique-internal-dockextras, force-continuity, expose-sticky-time, workspaces-edge-modifier-binding, wvous-{tl,tr,bl,br}-{corner,modifier}, digduration-{perframe,log,duration,angle}, NSAppNapLaunchDelay, IIOEnableOOP, NSTallLocalizedStrings, Session, Assistant;
- for every application tile opens the whole bundle for its code signature (`Contents/CodeResources`, `_CodeSignature/*`, `Info.plist`, `MacOS/<exe>`) and its `Contents/PlugIns/*.docktileplugin`; reads `/Library/Caches/com.apple.iconservices.store/*.isdata`, `~/.CFUserTextEncoding`, `~/Downloads`.
Our Dock must show the same set (the order of reading the keys and the per-tile bundle checks included) to be indistinguishable.

**Earlier idea, not needed now (interposer without root):** an interposer dylib (`__DATA,__interpose`, built with clang on the Mac) logs `bootstrap_look_up`, `bootstrap_check_in`, `xpc_connection_create_mach_service`, `open`/`stat` on paths, `CFPreferences*`, `notify_*`, `CFNotificationCenter` (distributed), `SLS*` calls. It is loaded with `DYLD_INSERT_LIBRARIES` through a copy of the agent plist (`EnvironmentVariables`) that we `launchctl bootstrap` into `gui/501` after `launchctl bootout` of the original. The Dock has no hardened runtime, so with SIP off this should be accepted: **not tried yet**.
**Compare:** the same interposer runs in ours; a script diffs the two logs (names and arguments, ids masked). The real Dock's log is the golden file (kept in `research/`, sanitised of the user's data).
**Replace:** the same plist mechanism with our binary.

## Blockers that need the user
- **Root on the Mac VM**: `sudo` works with the password `pear` (verified). Used for `dtrace`/`fs_usage` (a complete trace including paths the interposer misses) and for the boot-arg below.
- **AMFI:** our binary will carry the same private entitlements to be served by SkyLight, SystemUIServer and others; AMFI kills an ad-hoc signed binary with restricted entitlements. Likely needed on the Mac VM: `nvram boot-args="keepsyms=1 amfi_get_out_of_my_way=1"` and a reboot (root). Until then ours runs with the public API only and the private requests are refused: that is already a visible difference.

## Order
1. Capture the real Dock's trace with the interposer (golden). 2. Write the trace comparator. 3. New Dock skeleton on Cocoa: prefs through `CFPreferences`, the same tile model, the services answering minimally (tile size, magnification, orientation, hide, bounce). 4. Run it on the Mac VM in place of the real one, diff the traces, repeat. 5. The same source on pearOS (`open` AppKit + the stack of `d/`). 6. Look: pixel comparison against the real Dock on the same display.

## Owner decision (2026-11-26): wire-identical Dock and services
The Dock and every service it talks to are reimplemented to be identical **on the wire and in behaviour** with macOS 26.7.2: the same Mach / XPC messages byte for byte, the same SkyLight requests, the same CoreAnimation layer tree, the same files and preference keys. The code is ours (BSD-2-Clause, public); Apple's behaviour is learned by decompiling (REA) and by tracing on the Mac VM, and recorded as evidence. Not a function-by-function copy of Apple's machine code.
Check in both directions, for each service: Apple's client against our server, and our client against Apple's server; the trace comparator (`research/dock-trace/compare.py`) must show equal sets.
Order (one service at a time, each done before the next; the first run on pearOS showed IconServices blocking the start, see apps/dock-cocoa/README.md "On pearOS"):
1. **IconServices**: `iconservicesagent` (per user, `com.apple.iconservices`) and `iconservicesd` (`com.apple.iconservices.store`), the store files, the client protocol of IconServices.framework. Repository `IconServices`.
2. **LaunchServices**: `lsd` (`com.apple.lsd.mapdb`, `.modifydb`, ...) and `coreservices.launchservicesd`, replacing `d/.../lsd-stub`. Repository `LaunchServices`.
3. **com.apple.dock.\***: what the Dock provides (`dock.server` = CoreDock API, `dock.spaces`, `dock.fullscreen`, `dock.notificationcenter`, ...), in `apps/dock-cocoa`.
4. **usernoted.dock**: notification badges (push path).
5. Then the rest of the lookups in `DOCK-SERVICES.md`, in the order the real Dock's startup trace needs them.
