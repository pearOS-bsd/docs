# Repositories of pearOS (github.com/pearOS-bsd): what lives where

The rule: one repository = one thing that has its own build and its own tests; the pearOS build (`iso`) fetches the others by name (`pear_fetch NAME REF DIR`), never copies.

## Where everything lives now (done 2026-11-16)
| repository | what |
|---|---|
| `darwinator` | the kernel module that runs Mach-O programs (+ its tests) |
| `dyld` | machrun, the cache and framework tools, notes on the real dyld |
| `macdeps` | takes what Apple owns from the user's own Mac (scripts and lists only) |
| `IOKit` | user-space IOKit: hid-stub, registry data (the kernel half is in darwinator) |
| `tests` | cross-repository tests: real Mac apps on pearOS, smoke tests, test programs |
| `docs` | the documentation (users and developers, this file) |
| `d` | the daemons: `darwin/` (Mach-O: launchd, notifyd, wsbridge, lsd-stub, lsd-objc, svc-stub, carender-stub, wm-stub), `bsd/` (launchd + agents, usernoted, airportd, Open and Save Panel Service), `session/` (the scripts that start them) |
| `WindowServer` | wsd: compositor, backends, input, IPC, the client library, the test tools, tests, CI |
| `SkyLight` | the SkyLight protocol: wire headers, server handlers, client shim, generators, specs |
| `AppKit` | AppKit written back from the decompile + the backend (`Open*.m`) on wsd |
| `open` | the launcher (`open Notes.app`), `open-patch.py`, stubs, `deploy.sh`, `build-appkit.sh` |
| `QuartzCore` | CoreAnimation compat and the reference tests |
| `Solarium` | Liquid Glass (macOS 26): map of the Apple classes, the real parameters and defaults (REA), the Metal glass shaders and their translation to SPIR-V; implementation to come |
| `CoreUI` | the `.car` reader + `assets/` (Aqua, DarkAqua, DesktopServicesPriv); the big catalogues come from a Mac |
| `SDK` | compat frameworks and headers (`libwsbsdcompat`, CoreWLAN/CoreWiFi, UserNotifications, XPC ...), `foundation/`, `defaults/` |
| `LaunchServices` | icons (`LSIcon`, icns), UTI table, desktop pictures |
| `apps` | Dock, Finder, topbar (SystemUIServer), loginwindow, Terminal, TextEdit, KeyboardSetupAssistant, UITest |
| `iso` | builds the image: `build.sh` fetches every repository above into one workspace (copies laid out as the scripts expect) and builds; `overlay/ esp/ manifest/ ci/ ports/ dmg/`; the `iso.yml` workflow |
| `research` | decompile dumps and notes (`docs/`), probes and experiments (`tools/`, `lab/`), hand-over notes, old workflows |
| `CoreAudio`, `DisplayServices`, `IOPS`, `CoreWLAN`, `IOBluetooth`, `DoNotDisturb` | **planned, created 2026-11-18** (README only: scope, what the Control Center uses, plan, code to reuse): the frameworks behind the Control Center's controls. `CoreAudio` (devices, default output, volume; FreeBSD sound(4)), `DisplayServices` (private: brightness; backlight(8) / ACPI / soft dimming), `IOPS` (IOKit power sources: battery, AC; ACPI), `CoreWLAN` (takes over the shim in `SDK` + `d/bsd/airportd`), `IOBluetooth` (controller power, paired devices; netgraph), `DoNotDisturb` (private: Focus modes and assertions; verified API in its README; today a flag in `usernoted`) |
| `ploader`, `clevo_wmi`, `virtio`, `package-repo`, `pkgbuild`, `AppStore-Backend` | as before |
| `misc` | emptied: only a pointer; can be archived |

How the build finds them: `iso/build.sh` uses `D_DIR`, `SKYLIGHT_DIR`, `WINDOWSERVER_DIR`, `APPKIT_DIR`, `OPEN_DIR`, `SDK_DIR`, `QUARTZCORE_DIR`, `COREUI_DIR`, `LAUNCHSERVICES_DIR`, `APPS_DIR` when they point to a checkout, otherwise it downloads the branch (`PEAR_REF`, default `main`).
`open/deploy.sh` takes the repositories next to it (`../AppKit`, `../WindowServer`, `../SkyLight`, `../CoreUI`, `../research`) or `*_DIR`.  `WindowServer`: `make SKYLIGHT=../SkyLight`.

## The plan that led here (kept for the record)
## Exist and have their content (or get it now)
| repository | what | comes from |
|---|---|---|
| `darwinator` | the FreeBSD kernel module that runs Mach-O programs, its dyld (machrun), tests | stays |
| `d` | the daemons: `darwin/` (launchd, notifyd, wsbridge, lsd-stub, lsd-objc, svc-stub, carender-stub, hid-stub, wm-stub), `bsd/` (launchd + agents, usernoted, airportd, Open and Save Panel Service), `session/` (scripts that start them) | **done** (from darwinator and wsbsd) |
| `WindowServer` | wsd: compositor (software/GL), backends (KMS, fb, headless), input (evdev, touchpad, xkb), IPC, cursor, shadows, blur, the client library (libwsclient: `client.c`, `ws_client.h`), test tools (wsshot, wsclick, wskey, wswins ...) | wsbsd `src/` (without `sls_*`), `include/ws*.h`, `test/`, `tools/ws*.c`, `Makefile`, `man/`, `demo/` |
| `SkyLight` | our SkyLight: the SLS/CGS protocol (wire format, message ids, golden replies), the server side handlers `sls_*.c` that wsd links, the client shim (`SkyLight.h`, `skylight.c`), the generators (gen_golden, gen_blobs ...) and the specs/decompile notes | wsbsd `src/sls_*`, `include/SkyLight.h sls_*.h`, `shim/`, `docs/SPEC-SLS-WIRE.md skylight-*.txt EVENT-TAPS.md`, `tools/gen_*.py` |
| `AppKit` | AppKit of the Mac decompiled (`decompiled/src`: the classes) + the backend that puts it on wsd (`Open*.m`: windows, events, text, nib loader, documents, menus, panels, colours, theme) + its tests | wsbsd `appkit/` |
| `open` | the launcher of Mac applications on pearOS: `open Notes.app`, `open-patch.py` (rewrites load commands), stub generator (`gen-stubs.py`, `stubs-regenerate.sh`), `deploy.sh`, `build-appkit.sh` (builds /open/AppKit from the AppKit repo) | wsbsd `open/` |
| `iso` | the image build (FreeBSD base + overlay, esp, manifest, rc scripts, CI workflow) | wsbsd `iso/`, `ci/`, `.github/workflows/iso.yml` |
| `ploader`, `clevo_wmi`, `virtio` | boot loader, Clevo RGB driver, virtio graphics | stay |
| `package-repo`, `pkgbuild`, `AppStore-Backend` | packages, port recipes, App Store backend | stay |
| `misc` | what is left over; to be emptied and archived | |

## To create (so that nothing stays in `misc`)
| repository | what | comes from |
|---|---|---|
| `QuartzCore` | CoreAnimation compat: layers, the CA command stream decoder (`ca_scene`), the Core Animation render | wsbsd `quartzcore/`, `src/ca_scene.c`, `include/ca_scene.h` |
| `CoreUI` | the `.car` asset catalogue reader (coreui) and the asset tools (themes, icons, symbols) | wsbsd `coreui/` (the big `.car` files are fetched from the Mac, not stored) |
| `SDK` | the compat frameworks and headers that Mac sources are built against on FreeBSD (`libwsbsdcompat`, CoreWLAN/CoreWiFi, UserNotifications, XPC.m, frameworks.list, generators) | wsbsd `sdk/`, `foundation/`, `shim/` (rest), `defaults/` |
| `Dock` | our Dock (1:1 with the Mac's, decompile notes: `DOCK-DECOMPILED.md`, `DOCK-SERVICES.md`) | wsbsd `dock/` |
| `Finder` | our Finder and the desktop | wsbsd `finder/` |
| `SystemUIServer` | the menu bar and its status items (TopBar, menu mirror) | wsbsd `topbar/` |
| `LoginWindow` | the login window and the session start | wsbsd `loginwindow/` |
| `LaunchServices` | the LaunchServices pieces: icon (icns, LSIcon), UTI table, default applications | wsbsd `launchservices/`, `desktop-pictures/` |
| `Apps` | Terminal, TextEdit, KeyboardSetupAssistant, UITest ... (one folder each) | `terminal/ textedit/ ksa/ uitest/` of misc |
| `research` | what is not code: decompiled dumps, golden recordings, probes, the Mac lab (`lab/`, `docs/`, `tools/` probes) | wsbsd `docs/` (31 MB), `lab/`, `test/golden`, probes |

## Order of the move (each step leaves the build working: the pieces are fetched by `pear_fetch` or by `*_DIR` variables)
1. `d` (done).  2. `SkyLight` (WindowServer's Makefile takes `SKYLIGHT=../SkyLight`).  3. `WindowServer`.  4. `AppKit` and `open`.  5. `iso` (the workflow and the build script).
6. `QuartzCore`, `CoreUI`, `SDK`.  7. the programs (`Dock`, `Finder`, `SystemUIServer`, `LoginWindow`, `LaunchServices`, `Apps`).  8. `research`; `misc` archived.
