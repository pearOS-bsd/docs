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

## Who uses which spring (partial, 2026-11-18)
Reading the functions that use the Animation values (script: scan the binary for the global that each tiny initialiser stores into, find the functions that read it, list the log strings next to them):
- spring (0.4867, 1.0) at 0x10017d5c5 -> the **Live Activities** module of the menu bar: `LiveActivitiesController` "collapse %s" (`FUN_1001705e0`, `withAnimation(completionCriteria: .logicallyComplete)`) and "Expand %s at %s for %s" (`FUN_1001752a0`).
- spring (0.6283, 0.7333) at 0x1003ca984 -> the **banner** (SystemBanner): `didMoveMouse / hovering / visible`, "Dismissing banner via button", "Actually fading out ...".
- (0.33, 0.825) at 0x1003ca7e4 and 0x10052d9d7 -> views whose function holds only SwiftUI environment access strings (not identified).
So the ControlCenter **app** binary holds the menu-bar side (Live Activities, banners); the panel and its tiles are in `ControlCenter.framework` (and `ChronoUIServices` for the controls), inside the dyld cache. Extracted with `dsc_extractor` on the Mac VM for the same reading (the previous guess that the panel opens with (0.4867, 1.0) is therefore NOT supported by the code: it is the Live Activities collapse).
