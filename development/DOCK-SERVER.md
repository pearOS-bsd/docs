# com.apple.dock.server: what AppKit sends to the Dock (read on the Mac VM, macOS 26.7.2, 2026-11-16)

Method: our Dock (`apps/dock-cocoa`) is started as a launchd job whose plist declares `MachServices: com.apple.dock.server` (`research/dock-trace/dock-switch.sh`), checks in (`bootstrap_check_in`) and logs every message it receives (`touch /tmp/dock-server.debug` turns the log on: `/tmp/dock-server.log`, out-of-line data in `/tmp/dock-ool-<id>-<n>.bin`). Finder is restarted (`killall Finder`) or a window is minimized to make the system send messages.

## Messages seen (MIG style, subsystem base 96500: reply id = request id + 100)
| id | form | meaning (inferred) |
|---|---|---|
| 96519 | complex, 56 bytes, one port descriptor (a send right), NDR, two ints (0, a number that grows) | a client registers (the port is where the Dock can send to it); no reply |
| 96521 | simple, 40 bytes, expects a reply (reply port in `msgh_remote_port`, bits 0x1112), NDR, two ints (4, 0) | a query with selector 4; **if it gets no answer, the yellow (minimize) button of every window is greyed out**; answering `KERN_SUCCESS` + the int 1 (`DockServer.m`, a guess for the layout and value) turns it coloured again |
| 96508 | complex, 68 bytes, one out-of-line descriptor (81 920 bytes of which ~110 are data), NDR, ints (0, number, 0x14000, 1); no reply | a window is **registered** (sent when a Finder window is created, NOT by the minimize click). Data: `alea`, u32 3, u32 1, u32 0, u32 4 (dictionary), u32 entry count (2 or 3), u32 0, u32 0, then entries: key = u32 length, u32 0, UTF-16 characters; value of `title` = type, u32 length, u32 0, UTF-16 (the window title: `tmp`, `Applications`); `animate` = u32 2, u32 0 (false; present in one message only); `item` = u32 1, u32 3, u32 4, u32 0, **u32 window id** (0x224 = 548 matched `Finder id 548`). `apps/dock-cocoa/DockAlea.m` reads title, item, animate |

## What works with this
- Minimize button enabled (the answer to 96521). **Minimize itself does not happen**: the window stays on screen because our Dock does nothing with 96508 (the real Dock hides the window, plays the genie animation and adds a tile with the window image).

## What is missing to do the minimize
1. Decode the `alea` format (keys and value types; the window ids, the frame, the layer context / surface of the window image).
2. Take the window out of the screen and animate it: SkyLight transactions (`SLSTransactionOrderWindow` out, alpha / shape), the genie effect (`apps/dock/genie.c` has the maths from the old Dock), a minimized-window tile (window image through a SkyLight capture, `SLSHWCaptureWindowList`: prototype unknown).
3. Restore on click (the reverse message).
The values of 96521's reply are unverified beyond "the button turns coloured"; the real Dock's reply should be captured (dtrace on `mach_trap::mach_msg2_trap`, whose argument layout is not yet understood: the `syscall` provider sees none of these traps).

## Update (2026-11-16, later): the minimize click is not sent to the Dock's service
With the REAL Dock the yellow button minimizes the window (it goes to a small frame and the Dock gets a new tile with the window's thumbnail between the folder and the Trash). With OUR Dock in its place the same click changes nothing and **no message reaches `com.apple.dock.server`** (log empty). So minimizing is not driven through this service: it goes through the window server, which has to know which connection is the Dock. The real Dock makes these SkyLight calls at startup that ours does not: `SLSSetUniversalOwner`, `SLSSetConnectionProperty`, `SLSRegisterConnectionNotifyProc`, `SLSPackagesEnableConnectionWindowModificationNotifications`, `SLSSetDockRectWithOrientation`, `SLSSetBackgroundEventMaskAndShape`, `SLSWindowQueryCreate`; and it carries ~50 private entitlements (`com.apple.private.SkyLight.*`) that our ad-hoc signed binary does not. Most likely the window server serves the Dock role (minimize / window-modification notifications) only to a connection with those entitlements: this needs AMFI relaxed (`amfi_get_out_of_my_way=1` in the boot-args of the Mac VM + reboot), then our binary signed with the same entitlements. NOT tried.
