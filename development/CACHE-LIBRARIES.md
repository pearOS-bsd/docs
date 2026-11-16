# Libraries a cache of our own would need — and where we are (2026-11-16)

A dyld shared cache is built from the individual dylibs of the system (`cache_builder` of the dyld source takes them as input).  Today the 3625 images come from the Mac.
To build our own cache every image the programs need must be built by us (`clang -target x86_64h-apple-macos` + `ld64.lld`, or Xcode on the Mac VM) from source that may be redistributed.
Status: **started** (code in our repositories), **partial** (shim / reader / small part), **none** (we use the Apple binary from the cache).  "Open at Apple" = published at github.com/apple-oss-distributions (APSL 2.0 or the licence of the project).

| # | library / group | what it is | source | status today | repository to create |
|---|---|---|---|---|---|
| 1 | libsystem_kernel, libsyscall | system calls and Mach traps (user side) | open at Apple (xnu/libsyscall) | none; the kernel half is `darwinator` | `libsystem` |
| 2 | Libc (libsystem_c), Libm, libinfo, libresolv, copyfile, removefile | C library and friends | open at Apple | none | `libsystem` |
| 3 | libpthread, libplatform, libmalloc, libclosure | threads, atomics, malloc, blocks | open at Apple | none (workqueue emulation is in darwinator) | `libsystem` |
| 4 | libdispatch | GCD | open at Apple | none | `libdispatch` |
| 5 | libobjc (objc4) | the Objective-C runtime | open at Apple | none; `dyld/machrun/objc.c` maps ObjC 2 metadata onto the GNU runtime (old path, partial) | `libobjc` |
| 6 | libc++, libc++abi, libunwind, compiler-rt | C++ and unwinding runtime | open (LLVM) | none | `libcxx` (or fetch LLVM) |
| 7 | libxpc | XPC | headers open, implementation closed | partial: our own XPC over unix sockets (`SDK/src/XPC.m`) | `libxpc` |
| 8 | CoreFoundation | CF | open at Apple (older CF) / swift-corelibs | none (GNUstep corebase in the old path) | `CoreFoundation` |
| 9 | Foundation | NS* | closed (GNUstep base / swift-corelibs-foundation are alternatives) | partial: 3 classes written back (`SDK/foundation`: NSIndexPath, NSNull, NSSortDescriptor) | `Foundation` |
| 10 | CoreGraphics | Quartz 2D | closed (Opal = GNUstep alternative) | none | `CoreGraphics` |
| 11 | CoreText, ImageIO, ColorSync | text layout, image codecs, colour | closed | none | `CoreText`, `ImageIO` |
| 12 | QuartzCore | CoreAnimation | closed | **started**: 19 files (CALayer, CAAnimation, CATransaction, timing, transforms, raster, render) | `QuartzCore` (exists) |
| 13 | SkyLight | window server API | closed | **started**: 729 message ids known, ~200 handlers (server); client shim has 37 functions | `SkyLight` (exists) |
| 14 | AppKit | the UI toolkit | closed | **started**: 258 classes written back + `Open*` backend; 99 classes still missing (`research/docs/missing-ns-classes.txt`) | `AppKit` (exists) |
| 15 | UIFoundation | text system (NSTextStorage, layout managers, TextKit 1/2) | closed | none (taken from the cache; the biggest missing piece for AppKit) | `UIFoundation` |
| 16 | CoreUI | assets (`.car`), theme drawing | closed | partial: `.car` reader (`car.c`, `bvg`, `bitmap`, lzfse) | `CoreUI` (exists) |
| 17 | IconServices, IconFoundation | icons | closed | partial: shims in `SDK/src` | `IconServices` |
| 18 | CoreServices: LaunchServices, CarbonCore, FSEvents, AppleEvents | file types, apps, events | closed | partial: `LSIcon`, UTI table, `lsd-objc` (daemon), shims for FSEvents/AppleEvents | `LaunchServices` (exists), `CoreServices` |
| 19 | Security (+ Keychain) | crypto, keychain, code signing | open at Apple | partial: shims (`Security.c`, `Keychain.m`) | `Security` |
| 20 | SystemConfiguration, DiskArbitration, IOKit (user) | config, disks, hardware | open at Apple (configd, DiskArbitration, IOKitUser) | partial: DiskArb shim; `hid-stub` | `SystemConfiguration`, `IOKit` (exists) |
| 21 | CFNetwork, Network | networking | closed | partial: `NSURLSession.m` shim | `CFNetwork` |
| 22 | HIToolbox, HIServices, ApplicationServices | menus, events, Carbon | closed | none | `HIToolbox` |
| 23 | Private frameworks used by Finder/Dock/Settings | ~50 names: Accounts, CloudKit, Sharing, TimeMachine, UserManagement, ViewBridge, WidgetObservation ... | closed | partial: shims in `SDK/src` (old GNUstep path) | one repo `PrivateFrameworks` |
| 24 | Swift runtime (libswiftCore, Concurrency, Foundation overlays) | Swift | open (swift repo) | none | `swift-runtime` |
| 25 | libicucore, libxml2, zlib, sqlite3, libcurl ... | third-party | open | none | `thirdparty` |
| 26 | WebKit, JavaScriptCore | web | open | none | not planned |

## Reading the table
- Rows 1–7 (the system layer) have **open source at Apple**: a cache of our own could start there, built with our toolchain, and the kernel module would stop depending on Apple's libSystem.
- Rows 8–11 are the big ones (Foundation, CoreGraphics, CoreText): no open Apple source; alternatives: swift-corelibs-foundation + our own CoreGraphics.
- Rows 12–16 are what we already write (QuartzCore, SkyLight, AppKit, CoreUI).
- Row 15 (UIFoundation, the text system) is the largest missing piece for an AppKit that does not use the cache.
