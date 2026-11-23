# SwiftUI on pearOS: how a real AppKit / SwiftUI app reaches the screen, and where it stops today

Goal: macOS Swift / SwiftUI apps run on pearOS unchanged. pearOS runs the **real** AppKit, SwiftUI, RenderBox and QuartzCore of the Mac (from the dyld shared cache of the user's Mac, never in a repository) and replaces what is around them. Evidence, pass by pass: `github.com/pearOS-bsd/SwiftUI` (`docs/EVIDENCE.md`), Metal in `github.com/pearOS-bsd/Metal`.

## The four things a real AppKit window needs
1. **Window server protocol** (SkyLight): windows, spaces, transactions, events. `SkyLight/server`, `WindowServer`. The transaction decoder needs `WSD_OPSET=26` for the 26.7.2 cache.
2. **CoreAnimation render server** (`com.apple.CARenderServer`): the QuartzCore of the app sends the layer tree to it as command streams. Stand-in: `d/darwin/carender-stub`. It answers CASRegisterClient (40202), alignment (40254), max IOSurface size (40273), fence port (40208) and, after the register, sends the three notifications 0x9dd0..0x9dd2 that the real server sends. With them the app's commits (0x9c42) arrive.
3. **Metal** (`Metal`): RenderBox renders into IOSurface-backed textures. Device, queue, buffers and textures exist; command buffers, encoders, shaders, the Vulkan helper do not.
4. **Services around the app**: cfprefsd, LaunchServices (`lsd-stub`), appleevents, HID, uiintelligencesupport, fonts ... stand-ins in `d/darwin` and `IOKit`.

## Where it stops (2026-11-22)
What works on the lab VM (verified): AppKit windows with their content (title bar, content colour, menus: `SwiftUI/docs/appkit-hello-window.png`); a SwiftUI app (`tests/hello`) shows its window and menus; IOSurface (create, lock, look-up from another process: `darwinator/src/iosurface.c`, repo `IOSurface`); layer images in shared memory (memory-entry ports mapped by `carender-stub`); the geometry of layers as CoreAnimation has it; the window-visible notifications (906, 904, 912, 1201, 827) so that `NSWindow.occlusionState` is visible; the display timing page (`GetRealtimeDisplayDataShmemPort` 30504: refresh interval 16673320 ns) so that `NSScreen.minimumRefreshInterval` is 0.016673; precise `mk_timer` (48-byte expiry message, high resolution timers).
SwiftUI itself runs (`SwiftUI/tests/hosting`: an NSHostingView with a Text builds the same layers as on the Mac, with a 60 Hz display link).  What does not: the SwiftUI `Text` is not on screen because its layer contents are a **`CA::Render::ImageQueue`** (type 0x19, shared-memory ring + ports) that WindowServer does not read yet; the glyph masks are black, no traffic lights, one unsupported layer type; Metal executes nothing yet.
Metal: the shader translator exists (`pearOS-bsd/metal2vulkan`, the GPL-2.0-or-later fork, open source, a separate helper process: skill rule 17): Apple's `RenderBox` `default.metallib` compiles to verified SPIR-V; the runtime (Vulkan device, queues, IOSurface textures) is not connected.
Details and evidence of every step: `SwiftUI/docs/EVIDENCE.md` (passes 1-54).

## Needed in the lab VM (both easy to forget)
- the `darwinator.ko` of the repository, not the image's (`ulock_wait` must return the number of other waiters, else lost wakeups hang the app): `SwiftUI/tools/provision-vm.sh` step 0;
- 10 GB of RAM: every Mach-O process costs about 300 MB.

## Tools
`darwinator/tools/bp.c` (breakpoints in a Mach-O process on the lab VM through ptrace: registers at each hit; addresses = cache address + 0x1940c000), `lldb` on the Mac VM (`launchctl asuser 501`, `breakpoint set -a`, slide 0xeef9000), `msgtrace` (wraps SkyLight notification procedures, dumps the display state and the realtime display data page, IOKit calls), REA/Ghidra for QuartzCore / SkyLight / AppKit (`~/.pear/extracted`), `darwinator` debug levels (3: mk_timer, 4: kdebug_trace), `ipsw a2s` / `--symbols` for addresses.
`SwiftUI/tools/msgtrace.c` (interposer for a Mac: every Mach message, service names, render server messages, backtraces), `abortprobe`, `pearos-stack.sh`, `provision-vm.sh`; `CARENDER_TRACE=1` (exported before launchd) makes `carender-stub` print every message.


## Status 2026-11-22: SwiftUI draws
A hosting view with Text, Circle and Rectangle shows on pearOS (shapes and text). The system colours of SwiftUI (`Color.red`, `.primary`, ...) come from CoreUI's `DesignLibrary-macOS.bundle`; without it every one of them is clear and SwiftUI drops the layers. Take the bundle from the Mac (iso manifest and macdeps list it). Open: text mask position and tint, window chrome, dark appearance, Metal.

## Status 2026-11-23: interactive
`SwiftUI/tests/hello` (WindowGroup, Text, Button, Toggle, shapes) runs on pearOS, in the dark scheme, and reacts to a click: pointer events reach AppKit through the datagram stream (`GetPortStreamOutofline`, 30117) and the new text is drawn.  Open: control chrome (Button bezel, Toggle), window chrome, appearance from the system, keyboard/scroll, Metal.


## Status 2026-11-23 (end of the long session): what works, what does not, how to test
**Works on pearOS (real Apple SwiftUI/AppKit from the dyld cache):** a `@main App` with `WindowGroup`: Text (glyph masks with the colour of the scheme), `Button` (bezel), `Toggle` (box), shapes with colours and corner radius, window frame pieces (9-slice, rounded corners), traffic lights (active/inactive), dark scheme through `.preferredColorScheme`, a click on a Button changes `@State` and the new text is drawn, key events reach AppKit.
**Needed from the Mac (lab copies, never committed; the ISO manifest lists them):** `CoreUI.framework/Resources/DesignLibrary-macOS.bundle` (system colours: without it every `Color.red` is clear), `SwiftUI.framework/Resources/*`, `AppKit.framework/Resources/Assets.car`.
**Open (details in `SwiftUI/docs/EVIDENCE.md`, passes 55-92):**
* `NSScrollView` / SwiftUI `ScrollView`: AppKit's scroll-pocket code traps (a Swift force-unwrap of the design token `MPPocketFadeMinimumPocketAlpha`); pearOS lays the scroll view out after the window is attached, the Mac does not (passes 89-92).
* Text fields: focus starts the AutoFill remote view through ViewBridge services (`com.apple.ViewBridgeAuxiliary`, `com.apple.SafariPlatformSupport.Helper`) that do not exist; the failed handshake keeps the main thread busy (passes 79-83).  Plan: Apple's XPC services on demand under our launchd.
* `Toggle` check mark (CAShapeLayer), titlebar backdrop layers, appearance from the system preferences (`AppleInterfaceStyle` is not read), the real source of a window's frame (the Mac's AppKit centring rule is emulated in `SkyLight/server/sls_carender.c`), scroll/drag events, Metal.
**Test beds:** `SwiftUI/tests/hello` (Mac: `swiftc -parse-as-library -target x86_64-apple-macosx14.0`; options `-dark YES -focus YES -scroll YES -box YES -poke YES`), `SwiftUI/tests/hosting`, `SwiftUI/tests/appkit-hello` (`AKH_SCROLL=1`, `AKH_TOOLBAR=1`), clicks with `WindowServer/tools/wsclick` and `wskey` (`gmake wsclick wskey wswins`), event records with `SwiftUI/tools/evparse.py`, golden record test `WindowServer/test/test_evrec.c` (`gmake test_evrec`).
**Lab notes:** the first program started after a stack restart does not come up: start it twice; `/tmp` of the lab is 20 MB (trace files fill it); the Mac VM's `/tmp` is cleared at reboot (tools are rebuilt from the repo).
