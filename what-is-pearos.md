# What is pearOS BSD?

pearOS BSD is a desktop that looks and feels like a Mac and runs on **FreeBSD**, a free, fast and stable operating system.

You get:
- a Mac-style desktop: menu bar, Dock, Finder, windows, Control Center;
- the ability to **run Mac apps** (apps made for macOS) on it;
- all of it open and built from public sources.

How? Three ideas:
1. FreeBSD learns to run Mac programs (**darwinator**, **dyld**).
2. The screen, windows and menus are drawn by our own **window server** that speaks the same language as the Mac's (**WindowServer**, **SkyLight**).
3. The part of macOS that apps use for buttons, text and windows is rebuilt (**AppKit**) and apps are started with one command (**open**).

What it is not: it does not contain macOS.  Files that belong to Apple are taken from *your own* Mac by a script (**macdeps**), never shipped here.
