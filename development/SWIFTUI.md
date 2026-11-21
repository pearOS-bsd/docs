# SwiftUI on pearOS: how a real AppKit / SwiftUI app reaches the screen, and where it stops today

Goal: macOS Swift / SwiftUI apps run on pearOS unchanged. pearOS runs the **real** AppKit, SwiftUI, RenderBox and QuartzCore of the Mac (from the dyld shared cache of the user's Mac, never in a repository) and replaces what is around them. Evidence, pass by pass: `github.com/pearOS-bsd/SwiftUI` (`docs/EVIDENCE.md`), Metal in `github.com/pearOS-bsd/Metal`.

## The four things a real AppKit window needs
1. **Window server protocol** (SkyLight): windows, spaces, transactions, events. `SkyLight/server`, `WindowServer`. The transaction decoder needs `WSD_OPSET=26` for the 26.7.2 cache.
2. **CoreAnimation render server** (`com.apple.CARenderServer`): the QuartzCore of the app sends the layer tree to it as command streams. Stand-in: `d/darwin/carender-stub`. It answers CASRegisterClient (40202), alignment (40254), max IOSurface size (40273), fence port (40208) and, after the register, sends the three notifications 0x9dd0..0x9dd2 that the real server sends. With them the app's commits (0x9c42) arrive.
3. **Metal** (`Metal`): RenderBox renders into IOSurface-backed textures. Device, queue, buffers and textures exist; command buffers, encoders, shaders, the Vulkan helper do not.
4. **Services around the app**: cfprefsd, LaunchServices (`lsd-stub`), appleevents, HID, uiintelligencesupport, fonts ... stand-ins in `d/darwin` and `IOKit`.

## Where it stops (2026-11-21)
The app starts, the run loop works, windows are created but stay 1x1 and unordered; WindowServer never gets `TransactionCommitAsync` (30429). On the Mac it is preceded by 40209 (sent by `CA::Context::commit_transaction`) and by 40004 / 40005 (sent by `CA::Render::Fence::Transaction::Observer::activate`, a libdispatch mach source that fires when the server sends a message on the client's fence port). What the server sends on that port is the open question (decompiling QuartzCore).

## Needed in the lab VM (both easy to forget)
- the `darwinator.ko` of the repository, not the image's (`ulock_wait` must return the number of other waiters, else lost wakeups hang the app): `SwiftUI/tools/provision-vm.sh` step 0;
- 10 GB of RAM: every Mach-O process costs about 300 MB.

## Tools
`SwiftUI/tools/msgtrace.c` (interposer for a Mac: every Mach message, service names, render server messages, backtraces), `abortprobe`, `pearos-stack.sh`, `provision-vm.sh`; `CARENDER_TRACE=1` (exported before launchd) makes `carender-stub` print every message.
