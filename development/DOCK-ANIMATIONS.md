# Dock animations: what the real Dock does (measured on the Mac VM 26.7.2) and what ours does

Method: set the preference in the real Dock, move the pointer / launch an app / hide it, and read the accessibility tree (`~/bisect/ax`, AXUIElement positions) and screenshots; a sampling tool (`research/dock-trace/axpoll.c`, 200 Hz) for the time curves. The Mac VM has no GPU: effects that need the GPU (the genie warp) cannot be seen there, but everything the Dock lays out can be measured.

## Magnification (done in `apps/dock-cocoa/DockMagnify.m`)
Preferences `magnification` (bool), `largesize` (default 128), `tilesize`. Real Dock, tile size 46, largesize 80, 25 items, pointer at x = 100, 400, 640, 900, 1200 on the bar:
- slot of an item (distance between consecutive accessibility items) = 49.9 at rest, 83.6 under the pointer; as a function of the distance d between the pointer and the item's centre at rest: `slot(d) = 49.9 + (83.6 - 49.9) g(d)`, `g(d) = (1 + cos(pi (d / 175)^1.2)) / 2` for d < 175, 0 beyond (fit error under 0.6 px on 31 points). Peak slot = largesize + 3.6; the extra width of an item = largesize - tilesize - 0.3.
- separators grow too: 22.4 -> about 34.6 at the peak (0.415 of the icons' growth).
- the item under the pointer keeps the pointer at the same fraction of its slot (the rest follows): this reproduces the real item positions within 0.7 px for pointer positions 100...900 (3.6 px at 1200, where the real Dock clamps something at the right end: not modelled).
- the bar grows with the slots (list 1208 -> 1340 wide, x 36 -> -30 with the pointer in the middle: it extends past the screen edge), keeps its height (66), and the icons overflow it upwards: the icon's bottom stays on the baseline.
- the hover label rides on top of the magnified icon.
Not measured: the grow / shrink timing when the pointer enters / leaves (ours: eased over about 0.1 s), whether the range 175 depends on largesize / tilesize (assumed constant), the side orientations (implemented by symmetry, not compared).
