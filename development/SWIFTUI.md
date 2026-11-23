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
