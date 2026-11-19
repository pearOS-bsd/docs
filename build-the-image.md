# Build the image

On FreeBSD, as root:

```sh
git clone https://github.com/pearOS-bsd/iso && cd iso
sh build.sh            # fetches every repository by itself and writes the ISO into iso-out/
```

To build with your own checkouts, point the variables at them: `D_DIR`, `SKYLIGHT_DIR`, `WINDOWSERVER_DIR`, `APPKIT_DIR`, `OPEN_DIR`, `SDK_DIR`, `QUARTZCORE_DIR`, `COREUI_DIR`, `LAUNCHSERVICES_DIR`, `APPS_DIR`, `DYLD_DIR`.

## The Mach stack and the Control Center
`iso/build.sh` also builds the Mach-O daemons of `d/darwin` (notifyd, wsbridge, carender-stub, lsd-stub, svc-stub) and our Control Center (`apps/controlcenter-cocoa`, clang + ld64.lld on the open SDK) into `/usr/libexec/pearos`.  `rc.d/wsbsd_macstack` starts them when the owner's Mac frameworks are mounted; without them the Control Center of the top bar stays.
