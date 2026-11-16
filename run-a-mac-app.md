# Run a Mac app

```sh
open Notes.app                     # start an app from its bundle
open -a TextEdit /path/file.txt    # open a file with an app
open /path/file.txt                # open with the default app
```

What works today: TextEdit (window, typing, menus, copy/paste, Save), Stickies (the yellow note).  Not yet: apps written with SwiftUI, Chess, Terminal, Dictionary, third-party apps.

Where the app files come from: your own Mac (see the `macdeps` repository).  The system libraries come from the Mac's *dyld shared cache*; only AppKit is ours.
