# Licences: how the project stays BSD (2026-11-16)

**Goal:** what we write is **BSD-2-Clause**.  Code we take from others keeps its own licence (we cannot change it); the shipped system must not contain code that would force the combination under the GPL.

## Zones
| zone | contains | licences | rule |
|---|---|---|---|
| **ours** | `darwinator`, `dyld`, `d`, `SkyLight`, `WindowServer`, `AppKit`, `open`, `QuartzCore`, `CoreUI`, `SDK`, `apps` ... | BSD-2-Clause (ours) + MIT / ISC / Apache-2.0 / APSL-2.0 files kept as they came | any mix of these in one program is fine; APSL files stay APSL (changes published), Apache files keep their notices |
| **GNUstep (old path)** | `libgnustep-base`, `-gui`, `-back`, `-corebase`, Opal, GNUstep QuartzCore | LGPL-2.1 (checked on the sources: base 265 files LGPL, gui 326, back 103, corebase 52; one GPL-only file: `libs-gui/Source/GSIconManager.m`) | dynamic linking only, licence text and source offer in the image, the user can replace the library; never copy GNUstep code into our repositories |
| **Apple, closed** | the dyld cache, `/usr/lib/dyld`, `.car` of the Mac, binaries | Apple | taken from the user's own Mac by `macdeps`, never distributed |
| **GPL** | Darling, GNUstep tools and tests, FFmpeg built with x264, libdvdnav, libao ... | GPL | **not in the image**: a process that loads a GPL library becomes a GPL work, and the APSL files in the stack cannot be combined with GPL (the FSF lists APSL 2.0 as incompatible; APSL adds conditions the GPL forbids: notice in executables, publication of modifications for 12 months, termination if one sues Apple over a patent) |

Between zones the programs talk through IPC (the window server socket, XPC), never through shared code.

## The check
`iso/licenses/audit.sh ROOT` lists the libraries each shipped binary loads (ldd / otool -L; transitive ones count, a loaded GPL library is enough) and fails on GPL ones.  The table is `iso/licenses/libs.tsv`.

## Finding of the first run (the current GNUstep-path binaries on the test VM)
`Dock-gnustep` and `TopBar-gnustep` load **FFmpeg (libavcodec/libavformat ...) with x264, x265, libdvdnav, libdvdread, libao, libjbig**: all GPL (or GPL when built that way).  They come in through the FreeBSD `gnustep-base` / `gnustep-gui` packages.  So the image as built today has GPL libraries loaded into processes that contain our code.
Fix: build GNUstep without FFmpeg / DVD support (a package flavour or our own build in `iso/ci/gnustep-setup.sh`), or retire the GNUstep path.  The audit makes the build fail until this is done.

## Per repository
Every repository has `LICENSE` (BSD-2-Clause for our code) and, where it holds third-party source, `PROVENANCE.md` (origin, commit, licence, number of files).
