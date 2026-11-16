# Using the open-source code we collected (`upstream/`) inside our own code

Decision (2026-11-16): the code in `upstream/` is **meant to be used**, not only kept. Anything whose licence allows it is adapted into the `src/` of the layer that owns it. What is excluded is listed below, with the reason.

## How a file moves from `upstream/` to our code
1. **Search first** (`scripts/qdrant-search.py`, `where-is.sh`): maybe we already have it.
2. **Take only what a program on the VM needs now.** Whole trees are not copied: an Apple framework has thousands of files; we move the files that a real Mac program or our own stack calls, and test them on the FreeBSD VM before the next batch.
3. **Copy the file to `src/` of the owning layer keeping its licence header untouched.** Add below it a line `Modified for pearOS: <what and why>`. Never remove a copyright or licence line.
4. **Record it** in the repository's `PROVENANCE.md` (file, origin repository, commit, licence) and, for APSL files, in a `CHANGES` file next to them (APSL 2.0 asks that changes are documented). Apache-2.0 files: keep their `NOTICE` text and state the changes.
5. **The pristine copy stays in `upstream/`** until the adapted file has replaced it for good, so that `diff` shows exactly what we changed and a newer Apple release can be merged.
6. **Build and test on the VM, add a CI job, update docs and the skill** (RULES 9-11).
7. **The licence of the combined binary:** our files stay BSD-2-Clause, APSL files stay APSL 2.0 (file-level), MIT/BSD/Apache files stay as they are. All of these can live in one program. Nothing GPL or LGPL may be merged (`iso/licenses/audit.sh` checks the shipped binaries).

## What is allowed, per source (found by scanning every file's header on 2026-11-16)
| upstream | licence found in the files | verdict |
|---|---|---|
| `libsystem` (Libc, libmalloc, libplatform, libpthread, xnu-libsyscall, libclosure), `libdispatch`, `libobjc/objc4`, `CoreFoundation/CF`, `SystemConfiguration/configd`, `IOKit/DiskArbitration`, `IOKit/IOKitUser`, `CFNetwork`, `ravynos-IOKit`, `ravynos-SystemConfiguration`, `ravynos-CoreFoundation` | Apple APSL 2.0 (Libc also BSD: 908 files), libdispatch Apache-2.0, libclosure/libobjc2 MIT-style | **use** (keep headers, document changes) |
| `libdispatch/swift-corelibs-libdispatch` | Apache-2.0 | **use** |
| `libobjc/libobjc2` | MIT | **use** (a candidate runtime for our own Objective-C) |
| `ravynos-Foundation`, `ravynos-CoreGraphics`, `ravynos-CoreServices`, `ravynos-ApplicationServices` | MIT (Cocotron-derived: 652 of 738 files, 50 of 60, 12 of 13) | **use**; files without a header: see below |
| `PureDarwin-XPC` | APSL / BSD / Apache mix | **use**; one file mentions the GPL (`src/libxpc/xpc_error.c`), read it before moving it |
| `IOKitUser/IOCFUnserialize.tab.c` | bison output; the bison skeleton carries the GPL *with the exception that allows any licence for the generated parser* | **use**, but regenerate with a current bison if a doubt remains |
| `ravynos-Security` | Apple APSL 2.0 for most; `libsecurity_asn1`, `libsecurity_smime` (and `cmsutil.c`) come from Mozilla NSS and are offered under **MPL, GPL or LGPL** (tri-licence) | **use only what is needed**; for the NSS files we **choose the MPL** and keep the notice (MPL is file-level copyleft, compatible with a BSD project); we never choose GPL/LGPL |
| `ravynos-QuartzCore` (54 files) | **no licence header** in the files; PROVENANCE says "see the ravynOS repository" | **do not move yet**: first establish the licence per file (git history, the ravynOS LICENSE, Cocotron origin) and write it down |
| the same, ravynOS files without a header elsewhere | unknown per file | same: check before moving |

## Never merged (stay out of our tree, or are replaced)
| what | where | why | instead |
|---|---|---|---|
| FreeType source tree (20 MB) | `CoreGraphics/upstream/ravynos-Onyx2D/freetype` | third-party library, dual FTL / GPLv2 | link the system FreeType under its FTL (BSD-style) |
| gettext-tiny, autoconf / libtool scripts | `CoreText/upstream/ravynos-CoreText/gettext-tiny`, `Onyx2D/freetype/builds`, `*.m4`, `ltmain.sh`, `configure` | build-system files under the GPL (with exceptions) | our own `Makefile` |
| any file whose header says GPL or LGPL with no exception | found: none outside the two groups above and the NSS tri-licence files | would force the combined work under the GPL | not moved |
| Apple binaries, the dyld cache | the user's Mac | closed | `macdeps` |

## Order (proposal; start with what the next Mac program needs)
1. **Layer 1, the foundations that are Apple open source and small:** `libclosure`, `libplatform`, `libpthread`, `libdispatch`, `objc4` / `libobjc2`: needed by everything above; build on the FreeBSD VM against `darwinator`.
2. **`CoreFoundation` (CF)**: Apple's own, APSL; the base of Foundation.
3. **`Foundation` (ravynOS, MIT)**, `CoreGraphics` (Onyx2D minus FreeType), `CoreText`: the stack our own AppKit (`open`) stands on today with GNUstep pieces.
4. **`Security`, `SystemConfiguration`, `IOKit` user side, `CFNetwork`**: only the parts a program calls.

The real programs still run on the cache from the user's Mac; each framework we integrate is first built **next to** the cache and compared against it (`docs/development/CACHE-LIBRARIES.md`), and only then replaces it.
