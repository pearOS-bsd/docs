# ControlCenter replacement (pearOS ControlCenter in place of Apple's, macOS 26.7.2)

Goal (user, 2026-11-18): our own ControlCenter that can replace the real one on a real macOS, like `apps/dock-cocoa` does for the Dock; **same XPC services and same SkyLight calls** as the real one. Method = the Dock's: trace the real process with dtrace, reproduce, compare (`research/dock-trace/compare.py`), REA for what a trace cannot tell (prototypes, call sites).

## What the real ControlCenter is (Mac VM, 26.7.2)
- `/System/Library/CoreServices/ControlCenter.app`, launchd job `com.apple.controlcenter` (`/System/Library/LaunchAgents/com.apple.controlcenter.plist`): MachServices `com.apple.controlcenter.ccutil`, `com.apple.SystemBannerService`, `com.apple.SystemBanner`, `com.apple.controlcenter.controlcentermodule`, `com.apple.controlcenter.show.toggles` (HideUntilCheckIn), `com.apple.controlcenter.statusitems`, `com.apple.usernotifications.delegate.com.apple.controlcenter.notifications.airplay`; KeepAlive SuccessfulExit=false, ThrottleInterval 1, Aqua only. Unlike the Dock it IS an AppKit/SwiftUI app (links ControlCenter.framework, CoreWLANKit, CoreBrightness, DisplayServices, Focus, DoNotDisturb, SidecarCore, ...).
- It owns the **menu-bar status items** (windows at level 25, owner "Control Center": Spotlight 1063,0 31x30; Control Center icon 1094,0 42x30; clock/date 1136,0 144x30 on a 1280x800 display) and the **panel** (window level 22, 800,0 656x964 incl. margins; visible panel x 967..1273, y 35..561, opens on a click of the icon).
- Panel content (reference screenshot, no network/Bluetooth hardware on the VM): top "System recently" pill; Wi-Fi / Bluetooth / AirDrop tiles (state "Off"); Now Playing tile; Stage Manager and Screen Mirroring round buttons; Appearance (dark/light) button, Screenshot button, Focus pill; Display slider; Sound slider (+ AirPlay button); "Edit Controls" pill. Panel colour ~ (61,61,61), tiles (111,111,111) over a white desktop (material/blur not measured yet).

## Startup trace (research/cc-trace)
`capture.sh` = dtrace of the real process (`launchctl kickstart -k` while `dtrace -W` waits; `killall` does NOT work here: the trace stops after 5 lines); `real-controlcenter-startup-macos26.7.2.txt` (1864 lines: 34 LOOKUP, 84 XPCSVC lines, 1098 PREF, 226 SLS, 16 OBJC, 400 OPEN). `trace-ours.sh` + `cc-switch.sh ours|real|stop` run ours as job `com.pearos.controlcenter` (same MachServices as Apple's plist; Apple's job booted out) and trace it the same way. Always restore with `sh cc-switch.sh real`.

## Status
| kind | real | ours |
|---|---|---|
| LOOKUP | 13 | 13 same, same order |
| XPCSVC | 59 | 59 same, same order (5 of them are our own listeners) |
| PREF | 47 | 47 same |
| SLS | 226 | ~120 (status-bar windows + the startup queries; the rest is called inside SkyLight/AppKit or needs prototypes) |
| OBJC (CAContext) | 16 | 13 (addFence:, setPayload:, dealloc missing) |

## SkyLight: the status-bar path (dtrace args, `sbargs*.d`, results `sbargs*-real.txt`)
Each status item = `SLSNewWindowWithOpaqueShape[AndContext](cid, type 5, region, opaque, options 0x10000, tags, ...)` then `SLSSetWindowClientPerceivedType(cid, wid, 5, ...)`, `SLSCreateLayerContext` + `SLSSetWindowLayerContext`, `SLSSetWindowEventMask`, `SLSSetWindowTitle`/`SLSSetWindowProperty`, `SLSAddTrackingRegion`, then in ONE transaction: `SLSTransactionSetWindowTags` (x2), `SLSTransactionSetWindowShadowProperties`, `SLSTransactionSetWindowLevel(tx, wid, 0x19=25)`, **`SLSTransactionSystemStatusBarRegisterSortedWindow(tx, wid, sortKey, identifier, 0x590|0x490, 0|2)`** (sort keys 0x7ffffff5 and 0x7fffffe1: positions counted from the right edge), `SLSTransactionSystemStatusBarSetItemPrivacyIndicator`; afterwards `SLSSystemStatusBarGetWindowPreferredPosition(cid, wid, &out)`, `SLSCopySystemStatusBarMetrics`, `SLSPackagesSetWindowConstraints`. The 4th argument of RegisterSortedWindow is an object (the dump shows a string/UUID-like value): **REA (SkyLight pseudo-code, 2026-11-18): the prototype is `(tx, wid, int key, CFString ident, uint a, int b, float f, uint last)`** (opcode 0x3a in the transaction stream; the real ControlCenter does NOT call it itself: REA found no reference in the binary, AppKit's NSStatusBar does, `systemStatusBar` is imported); the other prototypes still to be taken with REA (thin x86_64 slice of the ControlCenter binary + SkyLight from the cache).
In the real process these are called by AppKit (NSStatusItem / NSStatusBarWindow); ours calls SkyLight directly (the Dock's method) so that it runs on pearOS's SkyLight too.

## Done 2026-11-18
Three status windows (Spotlight, Control Center, clock) at level 25 with drawn content, registered with the status-bar call; `CCSkyLightStartup.m` (table of the real startup queries), `CCPrefs.m` (47 keys), `CCServices.m` (59+13).

## Next
1. REA: prototypes of the remaining `SLSTransactionSystemStatusBar*`, `SLSCopySystemStatusBarMetrics`, `SLSSystemStatusBarGetWindowPreferredPosition`, `SLSPackagesSetWindowConstraints` (record in `apps/controlcenter-cocoa/SkyLightAPI`).
2. Three status windows (reuse `../dock-cocoa/DockWindow`), then the panel window; pixel diff against the real one (`research/dock-trace/pixdiff.py`).
3. PREF keys and the remaining SLS/CAContext calls until `compare.py` says same.
4. Behaviour: Wi-Fi/Bluetooth/AirDrop/Focus/Display/Sound through the same private frameworks on macOS, and through pearOS services on pearOS.
