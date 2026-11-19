# Build the image

On FreeBSD, as root:

```sh
git clone https://github.com/pearOS-bsd/iso && cd iso
sh build.sh            # fetches every repository by itself and writes the ISO into iso-out/
```

To build with your own checkouts, point the variables at them: `D_DIR`, `SKYLIGHT_DIR`, `WINDOWSERVER_DIR`, `APPKIT_DIR`, `OPEN_DIR`, `SDK_DIR`, `QUARTZCORE_DIR`, `COREUI_DIR`, `LAUNCHSERVICES_DIR`, `APPS_DIR`, `DYLD_DIR`.

## The Mach stack and the Control Center
`iso/build.sh` also builds the Mach-O daemons of `d/darwin` (notifyd, wsbridge, carender-stub, lsd-stub, svc-stub) and our Control Center (`apps/controlcenter-cocoa`, clang + ld64.lld on the open SDK) into `/usr/libexec/pearos`.  `rc.d/wsbsd_macstack` starts them when the owner's Mac frameworks are mounted; without them the Control Center of the top bar stays.

## Run the image in a VM (QEMU/KVM) and debug it
`iso/tools/run-vm.sh PEAROS.iso [CACHE.img]` opens a VM with a window (the cache disk is the owner's Mac frameworks made by `macdeps`).  The GPU is `virtio-vga` (`GL=1`: virgl): the image has a DRM/KMS driver for it and the window server follows the size of the QEMU window.  `-vga std` has no such driver and never resizes.  For debugging: `SERIAL=file:...` (or the default serial socket, login alex / pear), `SSH_KEY=key.pub` (a small GPT disk labelled EFISYS with `ssh.enable`, on the AHCI controller: the image has no USB mass storage driver, so a USB disk is not seen), the QEMU monitor socket (`screendump`, `mouse_move`).  A local build of the ISO takes minutes on a FreeBSD machine that already has the software (`SKIP_SOFTWARE=1`, see `iso/README.md`).
Known: with the screen as the only console and `boot_mute`, the boot froze at "Feeding entropy" on `virtio-vga`; the serial port is a console too in `loader.conf` now.  The pear boot logo of the kernel needs `WindowServer/src/splash_pear.inc` (`iso/tools/patch_vt_logo.py`).
