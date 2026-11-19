# What is pearOS BSD?

pearOS BSD is an **open-source implementation of macOS** on **FreeBSD**, a free, fast and stable operating system.  It is not a desktop that merely looks like a Mac: every part speaks the same protocols, uses the same file formats and behaves the way the real one does, so that real Mac programs and real Apple frameworks work with it and the other way round (what we write can replace the Apple part it stands for).

You get:
- a Mac-style desktop: menu bar, Dock, Finder, windows, Control Center;
- the ability to **run Mac apps** (apps made for macOS) on it;
- all of it open and built from public sources.

How? Three ideas:
1. FreeBSD learns to run Mac programs (**darwinator**, **dyld**).
2. The screen, windows and menus are drawn by our own **window server** that speaks the same language as the Mac's (**WindowServer**, **SkyLight**).
3. The part of macOS that apps use for buttons, text and windows is rebuilt (**AppKit**) and apps are started with one command (**open**).

What it is not: it does not contain macOS.  Files that belong to Apple are taken from *your own* Mac by a script (**macdeps**), never shipped here.
