# What already exists — and what we took (survey of 2026-11-16)

Goal of the survey: not to repeat what others have done, to reuse what a licence lets us reuse, and to know exactly where it came from.
Licences were read from the repository metadata and from the file headers (the GitHub API names are given); where a licence could not be confirmed it says so.  **This is an engineering note, not legal advice.**

## The rule we follow
| licence | what we do |
|---|---|
| MIT, BSD, ISC, Apache-2.0 | may be copied into our repositories with the licence file kept (`upstream/`, see each `PROVENANCE.md`) |
| APSL 2.0 (Apple Public Source License: the Apple open-source releases) | may be copied and redistributed with the notices kept; changes to those files must stay published (our repositories are public) |
| LGPL (GNUstep Opal, QuartzCore) | referenced, not copied into our tree; used as a library only if a build needs it |
| GPL (Darling, GNUstep base / gui / back, corebase) | **not copied**: only read as documentation of how a problem was solved |
| closed (Apple binaries, `.car` files, the dyld cache) | never copied; taken from the user's own Mac by `macdeps` |

## The projects
| project | what it is | licence | state | what we use from it |
|---|---|---|---|---|
| **ravynOS** (formerly Airyx; github.com/ravynsoft/ravynos) | FreeBSD base + a macOS-like desktop + its own Cocoa-style frameworks (Foundation, AppKit, CoreGraphics/Onyx2D, CoreText, QuartzCore, CoreServices, Security, SystemConfiguration, CFNetwork, IOKit ...) | MIT for the frameworks (from Cocotron, headers kept), BSD for the base, CFLite under APSL | active (last push 2026-09) | **copied** (sources only) into `Foundation`, `CoreGraphics`, `CoreText`, `CoreServices`, `Security`, `SystemConfiguration`, `CFNetwork`, `HIToolbox` (ApplicationServices), `IOKit`, `CoreFoundation`, `QuartzCore`.  Not copied: its AppKit (398 files, Cocotron-era API; our AppKit is written back from the real one), its FreeBSD tree |
| **Darling** (github.com/darlinghq/darling) | runs macOS programs on Linux: XNU as a Linux module, Cocotron-based AppKit/Foundation, Apple open source pieces | GPL-3.0 overall (XNU part APSL) | very active | **read only** (GPL): how they emulate Mach IPC, `launchd`, the cache-less frameworks, `lsd`/LaunchServices; no code copied |
| **NextBSD** (github.com/NextBSD/NextBSD) and the revival **nextbsd-redux** | FreeBSD with Mach IPC, launchd as PID 1, libdispatch, notifyd, asl, IORegistry, configd, IPConfiguration, libxpc | BSD-2-Clause | active again in 2026 | **the closest to our `darwinator` + `d`**: its PORTING.md and ports of launchd / notifyd / configd / the IOKit registry are the reference for `d` and `IOKit` (BSD-2: can be copied when we need a piece); its libxpc carries ravynOS enhancements |
| **pkgdemon/freebsd-launchd-mach** | launchd-842 + libdispatch + libxpc on a Mach kernel module for FreeBSD | BSD-2-Clause | active | reference for `d/darwin/launchd` and `libxpc` |
| **PureDarwin/XPC** | an open-source XPC and launchd based on launchd 842.91.1 | APSL per file | archived (2024), incomplete by its own README | **copied** into `libxpc/upstream` (without its `headers/` folder: those are SDK headers) |
| **relaunchd** (mheily) | a portable launchd clone (ISC) | ISC | idle since 2023 | reference only |
| **Apple open source** (github.com/apple-oss-distributions: xnu, Libc, libpthread, libplatform, libmalloc, libclosure, libdispatch, objc4, CF, configd, IOKitUser, DiskArbitration, Security, dyld ...) | the parts of Darwin that Apple publishes | APSL 2.0 / Apache-2.0 | current (macOS 26 sources, mostly June 2026) | **copied** into `libsystem` (Libc, libpthread, libplatform, libmalloc, libclosure, xnu/libsyscall), `libdispatch`, `libobjc` (objc4), `CoreFoundation` (CF), `SystemConfiguration` (configd), `IOKit` (IOKitUser, DiskArbitration).  `dyld` has its own plan |
| **swift-corelibs-libdispatch / -foundation** (swiftlang) | libdispatch and Foundation of Swift for Linux and BSD | Apache-2.0 | active | libdispatch **copied** (it already has FreeBSD support); swift-corelibs-foundation is Swift code: kept as a reference |
| **Cocotron** (github.com/cjwl/cocotron) | Cocoa for Windows (Foundation, AppKit, CoreGraphics, Onyx2D) | MIT | frozen since 2015, but alive inside ravynOS and Darling | taken through ravynOS (above) |
| **GNUstep** (libs-base, gui, back, corebase, opal, quartzcore, libobjc2) | OpenStep / Cocoa on Unix | libs-base GPL-2, gui/back/corebase GPL-3 (their library code is LGPL-2.1+ per the packagers), opal and quartzcore LGPL-2.1, libobjc2 MIT | active | libobjc2 (MIT) **copied** as a reference runtime; the rest is the *old path* of this project (GNUstep + Opal); not copied |
| **helloSystem** | FreeBSD desktop with a Mac look (Qt) | mixed | slow since 2024 | ideas for the menu bar and the desktop; no code |
| **Gershwin** (GNUstep desktop on GhostBSD), **NEXTSPACE** (NeXT-like desktop on Linux) | desktops over GNUstep | GNUstep licences | Gershwin active, NEXTSPACE stalled | ideas only |
| **PureDarwin / OpenDarwin / Darwin XNU builds** | bootable Darwin from the Apple sources | APSL | PureDarwin slow | the XNU pieces we need are already in the Apple sources above |
| **NeXTSTEP / OpenStep** | the 1990s system everything above descends from | closed (the OpenStep *specification* is public) | historic | the API shape (AppKit, Foundation) as documented; nothing copied |

## What each repository got
See `PROVENANCE.md` in the repository: `libsystem`, `libdispatch`, `libobjc`, `libxpc`, `CoreFoundation`, `Foundation`, `CoreGraphics`, `CoreText`, `CoreServices`, `Security`, `SystemConfiguration`, `CFNetwork`, `HIToolbox`, `IOKit`, `QuartzCore`.
Empty on purpose (nothing open to start from): `ImageIO`, `UIFoundation`, `IconServices`, `PrivateFrameworks`, `swift-runtime` (fetch the Swift toolchain), `libcxx` (LLVM), `thirdparty` (ICU, libxml2, zlib ... fetched, not copied).

## What this changes in the plan
1. **NextBSD-redux is a competitor and a source at the same time**: Mach IPC and launchd inside the FreeBSD kernel versus our `darwinator` (a module that runs the real Mac dyld and libSystem).  Worth a comparison of the Mach IPC and IOKit registry code; a convergence on one kernel-side layer would save work.
2. **ravynOS has already written most of the second-tier frameworks** (Foundation, CoreGraphics, CoreText, SystemConfiguration, CFNetwork under MIT).  For a cache of our own these are the base of rows 8–11 and 20–21 of `CACHE-LIBRARIES.md` — but they are Cocotron-era (2008) APIs, so every class still has to be checked against the real behaviour before it replaces the Apple binary.
3. **Nobody has the text system (UIFoundation) or SkyLight**: those stay ours.
