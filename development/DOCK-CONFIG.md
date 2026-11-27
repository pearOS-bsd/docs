# The Dock's configuration on the real Mac (macOS 26.7.2) and where ours differs

Evidence 2026-11-16: `~/Library/Preferences/com.apple.dock.plist` of the Mac VM (read with `plutil -convert xml1`), and the strings of `Dock` (x86_64 slice, Ghidra via REA). Nothing here is guessed; what is not known is marked **unknown**.

## The file
`~/Library/Preferences/com.apple.dock.plist`, domain `com.apple.dock`, read and written through `cfprefsd`. On a Mac that was never customised the file contains only:

| key | type | example | meaning |
|---|---|---|---|
| `version` | int | `1` | required: without it the tiles are not built (earlier finding) |
| `mod-count` | int | `4` | number of times the Dock saved its layout (**unknown** whether anything reads it) |
| `loc`, `region` | string | `en_US:GB`, `GB` | locale the layout was made for |
| `persistent-apps` | array of tiles | 18 tiles | the left (application) side |
| `persistent-others` | array of tiles | 1 `directory-tile` (Downloads) | the right side (folders, files) |
| `recent-apps` | array of tiles | 1 tile | the "recent applications" section |
| `wvous-br-corner` | int | `14` | hot corner bottom right (action 14 = Quick Note) |
| `last-analytics-stamp` | array of one real | `815944343.97` | analytics |

Settings such as `tilesize`, `magnification`, `orientation` are **absent** when they have their default: the Dock registers the defaults itself.

## A tile
`{ GUID: int, tile-type: string, tile-data: dict }`. `tile-type` seen: `file-tile` (applications, 18 + 1), `directory-tile` (a folder). Others exist in the binary (`spacer-tile`, `small-spacer-tile`, ... **unverified here**).

`tile-data` of a `file-tile`: `book` (data: a bookmark), `bundle-identifier` (string), `dock-extra` (bool), `file-data` (dict: `_CFURLString` = `file:///...app/`, `_CFURLStringType` = 15), `file-label`, `file-mod-date` (int, seconds since 1904: HFS epoch), `file-type` (int: 41, 169, 1 seen; **unknown** meaning), `is-beta` (bool), `parent-mod-date` (int).
Extra keys of a `directory-tile`: `arrangement` (2), `displayas` (0), `showas` (1), `preferreditemsize` (-1); its `file-mod-date` has another form (a large integer).

## Keys the Dock binary reads (strings found at these addresses, `Dock` x86_64)
`tilesize`, `largesize`, `magnification`, `magnify-immutable`, `orientation`, `autohide`, `autohide-delay`, `launchanim`, `show-recents`, `static-only`, `minimize-to-application`, `show-process-indicators` (and the Obj-C properties `tileSize`, `largeSize`, `autoHide`). The default values are **unknown**: the registration code is reached through `__cfstring` constants that Ghidra does not cross-reference; finding it needs the registerDefaults call traced dynamically (Frida on the Mac) or by hand in Ghidra.

## The old GNUstep Dock (`apps/dock/Dock.m`, `loadPrefs` / `savePrefs`; removed 2026-11-27: the current code is `apps/dock-cocoa/DockPrefs.m`)
| key | ours | note |
|---|---|---|
| `tilesize`, `largesize`, `magnification`, `orientation`, `autohide`, `autohide-delay`, `autohide-time-modifier` | read | our default tile size 58 / large 99 is a measurement of the real Dock on 1280x800, not the registered default |
| `persistent-apps`, `persistent-others` | read, written back (Finder and Apps tiles are kept out of the file) | the written tiles lack `bundle-identifier`, `dock-extra`, `file-type`, `file-mod-date`, `parent-mod-date`, `is-beta`, `book` |
| `version`, `mod-count`, `loc`, `region`, `wvous-*`, `recent-apps` | not interpreted; unknown keys are kept on write | `version` is not written: a plist saved by us would not satisfy the real Dock |
| `launchanim`, `show-recents`, `show-process-indicators`, `minimize-to-application`, `static-only`, `magnify-immutable` | **missing** | |
| read path | `dictionaryWithContentsOfFile:` of the file directly | the Mac reads through cfprefsd (so that `defaults write` and other programs see changes at once); ours does not use cfprefsd |

## Next steps, in order
1. Trace the registered defaults of the real Dock (Frida `observe_native_calls` on `-[...registerDefaults]` / `CFPreferencesSetAppValue` on the Mac VM) and write them into this file.
2. Make our writer produce the same tile shape (the fields above; `bundle-identifier` from the app's Info.plist; `version` 1; the unknown ints stay absent until understood).
3. Read the preferences through cfprefsd (`d/session`) and observe `com.apple.dock.prefchanged`, like the real Dock.
4. The services (`DOCK-SERVICES.md`): first `com.apple.dock.server` with tile size, magnification, orientation, hide and bounce, then LaunchServices for the running-application dots.
