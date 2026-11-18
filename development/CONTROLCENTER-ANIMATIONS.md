# ControlCenter animations: taken from the code (REA), not measured

Why not measured: the real panel is SwiftUI (RenderBox); its animations are not in the CoreAnimation stream (a capture of the real ControlCenter's commits while the panel opens has no animation records), and the Mac VM has no GPU, so frame sampling there (`research/cc-trace/animprobe.c`) only shows the VM's rendering latency (about 250 ms until the panel's shapes appear, content by 400 ms, no visible scale or slide at that resolution).
Method: the thin x86_64 slice of `/System/Library/CoreServices/ControlCenter.app/Contents/MacOS/ControlCenter` in REA (Ghidra); the SwiftUI functions it imports for animation (`strings`): `Animation.spring(response:dampingFraction:blendDuration:)`, `interpolatingSpring(mass:stiffness:damping:initialVelocity:)`, `timingCurve`, `easeInOut(duration:)`, `easeOut(duration:)`, `linear(duration:)`, `.default`, `.delay`; `AnyTransition.opacity` / `.asymmetric`, `ContentTransition.numericText` / `symbolEffect` / `symbolReplace`, `GlassEffectTransition`. `find_xrefs_to_name` gives the call sites; each one is a tiny function that loads its constants from the data section into xmm0..xmm3 and stores the Animation in a global (a `static let`); the constants were read from the file with a script (REA `procedure_assembly` for the first one, then the bytes).

## Constants found (x86_64 ControlCenter, macOS 26.7.2)
`Animation.spring(response, dampingFraction, blendDuration)`, 22 call sites:
| response | dampingFraction | sites |
|---|---|---|
| 0.4867 | 1.0 | 0x10017d5c5, 0x10036ead7, 0x100372752, 0x100373f61 (and with blend 0: 0x10036eb53, 0x10036ebcf) |
| 0.5 | 1.0 | 0x10018bc34, 0x1001dc4be, 0x1002fb800, 0x1003bd9ed |
| 0.5 | 0.85 | 0x100230eb3, 0x100446cc2, 0x10049d9ba, 0x1004c3375, 0x10058f7aa |
| 0.33 | 0.825 | 0x1003ca7e4, 0x10052d9d7 |
| 0.33 | 1.0 | 0x10026de1c |
| 0.15 | 0.85 | 0x1001dc3ab |
| 0.5 | 0.3 | 0x10048fdc7 |
| 0.6283 | 0.7333 | 0x1003ca984 |
`interpolatingSpring(mass, stiffness, damping, initialVelocity)`: (2.0, 300.0, 50.0, v?) at 0x1004ff512; (1.0, 6.2832 = 2 pi, ..., v?) at 0x100213012. `easeInOut(duration)` at 0x1002d0a24, `easeOut(duration)` at 0x1002d1159, `linear(duration)` at 0x100093c60 / 0x100093c93: the durations are not in the data section next to the call (computed or passed in a register): not read yet.
SwiftUI's presets for comparison: `.smooth` = response 0.5 critically damped, `.snappy` = 0.5 / 0.85 (damping fraction), `.bouncy` = 0.5 / 0.7; (0.15, 0.85) is the interactive spring (drags, presses).

## What ours does (`apps/controlcenter-cocoa`)
`CCSwiftUISpring(keyPath, response, damping)` builds a `CASpringAnimation` with stiffness (2 pi / response)^2, damping 2 zeta sqrt(stiffness), mass 1. The panel opens with scale (from 94 % about its top-right corner: a guess) and opacity on the spring (0.4867, 1.0) (the most used). NOT identified: which call site belongs to which effect (the sites are anonymous static values: the owners are found through the globals they are stored in, or the Swift metadata of the views in `ControlCenter.framework` / `ControlCenterUIKit`). The fade-out (0.12 s), the cross-fade of pages and edit mode (0.15 s) and the state changes are approximations. Next: map the globals to their uses (REA xrefs to the stored globals, e.g. 0x1008449d0 for the first site), and read the durations of the three timing-curve sites.

## Who uses which animation (read from the functions around each call site, 2026-11-18)
The app binary DOES hold the panel's SwiftUI (BentoBox, sliders, modules); `ControlCenter.framework` is only 300 KB. Method: the function that contains each call site and the strings it references (os_log formats, accessibility ids, SF Symbol names):
| animation | where (function: strings) | meaning |
|---|---|---|
| spring (0.5, 0.85) = `.snappy` | 0x100446c18 "Display %u changed hasBrightnessControl"; 0x10049d73e "AXKeyboardBrightnessSlider"; 0x1004c2fb5 "arrow.uturn.backward", "controlcenter-airplay"; 0x10058f4ac "AXBackgroundSoundVolumeSlider", "music.quarternote.3"; 0x100230da2 | a control's value changes (sliders, AirPlay, background sound) |
| spring (0.33, 1.0) | 0x10026ddc9 "expand %s" / "collapse %s" | expanding / collapsing a module |
| spring (0.4867, 1.0) | 0x1001705e0 "collapse %s", 0x1001752a0 "Expand %s at %s for %s" (Live Activities); 0x100373e97 "[SystemBannerController] Actually faded out" | live activities and banners |
| spring (0.6283, 0.7333) | 0x1003738c9 "Dismissing banner via button", "didMoveMouse ... hovering ... visible" | banner dismissal |
| spring (0.5, 1.0) = `.smooth` | 0x1003bd764, 0x1002fb57f, 0x10018bc11, 0x1001dc446 (environment-reading views) | view transitions (not individually identified) |
| spring (0.15, 0.85) | 0x1001dc32d | interactive (drag, press) |
| spring (0.5, 0.3) | 0x10048fc4b | a bouncy one-off (not identified) |
| interpolatingSpring (mass 2, stiffness 300, damping 50) | 0x1004ff4f3 "modalAnchoredFromDisplayable(" | **a page / modal anchored to its source control: the Wi-Fi, Bluetooth, Sound ... pages** (critically damped: zeta = 50 / (2 sqrt(300 * 2)) = 1.02, omega 12.2 rad/s, settles in about 0.4 s) |
| interpolatingSpring (mass 1, stiffness / damping computed at run time) | 0x100212f8c "Choose Content to Share", "controlcenter.show.toggles", "notificationcenterui.menu" | showing the panel (`show.toggles`) and menus: parameters not readable statically |
| easeInOut(duration) | 0x1002d0a18 symbols "waveform.and.mic", "person.fill.viewfinder" (recording-indicator style views) | duration not read |
| easeOut(duration), linear(duration) | 0x1002d114d, 0x100093c31 | not identified |
Used in ours: the page opens with the real `interpolatingSpring(2, 300, 50)` (scale from 96 % about the panel's corner: the 96 % is a guess); the panel opens on the smooth spring (0.5, 1.0) (a guess among the candidates: the real `show.toggles` spring has run-time parameters); state changes cross-fade 0.15 s (the real: `.snappy` on the value: not possible for a bitmap tile). The earlier note that the panel opens with (0.4867, 1.0) was wrong: that value belongs to Live Activities and banners.
