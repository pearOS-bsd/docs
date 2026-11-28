# Roadmap: running without the owner's Mac (written 2026-11-20)

**Goal:** the image must not need any file taken from a Mac.  The Mac stays only as the *oracle* for tests (compare our behaviour with Apple's, wire and ABI), never as a build or runtime dependency.  Same rule as always: do what Apple does (same protocols, ABI, file formats), no own protocol as a shortcut, no Apple file in any repository, no GPL/LGPL code copied.

## What comes from the Mac today (the `MACCACHE` disk, made by `macdeps`; mounted by `iso/overlay/etc-rc.d-wsbsd_macdeps`)
| file | used for | replaced by |
|---|---|---|
| `dyld` (thin x86_64 slice of `/usr/lib/dyld`) | runs every Mach-O program (the kernel module `darwinator` hands the file to it) | step 2 |
| dyld shared cache (`Preboot/Cryptexes/OS/System/Library/dyld/`) | all the libraries and frameworks of the Mach-O programs | step 3 (a cache is only an optimisation, step 5) |
| `cfprefsd` | preferences (CFPreferences / NSUserDefaults of every Mach-O program; without it each read waits) | step 1: done, `d/darwin/cfprefsd` (2026-11-28) |
| `Fonts/` (SF, Helvetica, LastResort ...) and SF Symbols data | text and symbols of the Mac programs | step 4 |

## Steps, in order
1. **`cfprefsd` of our own** (small, high value).  A daemon in `d` that speaks the same XPC protocol as Apple's (`com.apple.cfprefsd.daemon` / `.agent`), the same plist files under `~/Library/Preferences` (and `ByHost`), the same change notifications.  Measure Apple's with the Mac VM (message ids, keys, replies), check both ways: Apple's clients against ours, ours against Apple's tools (`defaults`).  Test: Control Center's layout files, `defaults read/write`.
2. **dyld built from source.**  `dyld/upstream/dyld` (dyld-1378, APSL 2.0) built with `clang` + `ld64.lld` for a Mach-O target.  It needs no shared cache here (`dyld/docs/OWN-CACHE.md` section 1: the "no cache" halts are only in the pid 1 ignition path; `kern.darwinator.use_cache=0`).  Then `/usr/lib/dyld` is ours.
3. **The libraries, one by one, on disk, `use_cache=0`.**  libSystem, libdispatch, libobjc, libc++/libc++abi, libxpc, CoreFoundation, Foundation, CoreGraphics, CoreText, ImageIO, Security, SystemConfiguration, CFNetwork, CoreServices, LaunchServices, IconServices, CoreUI, QuartzCore, HIToolbox, AppKit ... (the layers of `DEPENDENCIES.md`).  `/open` already builds AppKit, Cocoa and stand-ins from the open sources (`dyld/tools/sdk/build-open-sdk.sh`).  Method: put our dylib first in the search path, run the program, compare with the Mac (differential tests in `tests`); goal for the first milestone: Dock, Finder and Control Center run on our libraries only.
4. **Fonts and symbols.**  Apple's fonts and SF Symbols cannot be redistributed.  Needed: free substitutes (e.g. Inter or similar for text, an open icon set mapped to the SF Symbol names for the glyphs) with the same metrics where possible.  **Open decision for the owner:** "exactly like Apple" and the licence collide here.
5. **A dyld shared cache of our own** (last; optimisation for start time and memory).  Either port Apple's `cache_builder` (needs xnu external headers, a replacement for `mach_vm.h`, hash functions) or write a minimal writer from `dyld_cache_format.h`.

CoreAudio / AudioToolbox / AVFoundation (own implementations, wire-compatible `coreaudiod` in `d`) are part of step 3 and are planned in `CoreAudio/README.md`.

## Step 1 done (2026-11-28)
`d/darwin/cfprefsd` is our cfprefsd: both roles (`com.apple.cfprefsd.agent` per user, `com.apple.cfprefsd.daemon` for the system), the operations of Apple's (read/write, multi-message, observe, flush, path, user deleted, synchronize), the shared memory counters with Apple's slot formula, change notifications, deferred atomic writes of the Mac's plist files.  The protocol comes from decompiling CoreFoundation-5026.6.7.5 and recording the Mac's traffic (`research/docs/CFPREFSD-WIRE.md`).  Checked both ways on the Mac VM in Apple's test mode (Apple's CoreFoundation, Foundation and `defaults` against ours: the same messages, slots and files as against Apple's) and on the FreeBSD lab VM (the Mac's CoreFoundation from the dyld cache against ours, started on demand by our launchd).  The image now starts ours (`iso/overlay/etc-rc.d-wsbsd_macstack`); the Mac's copy on the cache disk is only a fallback.  Apple's agent was also replaced inside a real macOS session (GPU VM, SIP off): Finder, Dock, Calculator, TextEdit and `defaults` run on ours.  `PlistDiff`/`PlistFD` are sent like Apple's.  Open: cloud sources, the quarantine xattr on macOS.

## Done / not done (2026-11-20)
* Done: the Mac side starts from the cache disk in the image (macdeps rc script), Control Center of ours runs on it.
* Not started: steps 1, 2, 4, 5.  Step 3: only `/open` (AppKit, Cocoa, stand-ins) and the open sources in `upstream/` of the runtime repositories.

## How a new session continues
Start with step 1 (cfprefsd) and step 2 (dyld); record every measurement of Apple's behaviour next to the code; update this file and `pearos-skill/skills/pearos/STATE.md` at each milestone.
