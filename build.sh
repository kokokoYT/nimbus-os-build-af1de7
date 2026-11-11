#!/bin/bash
# Build the Nimbus OS (Debian based) ISO. Run on a Debian 12 / Ubuntu x86-64 machine with internet.
set -e
sudo apt-get install -y live-build debootstrap squashfs-tools xorriso
cd "$(dirname "$0")"
# files uploaded through a web browser lose their "executable" flag and may get Windows line endings: repair both
find . -type f ! -name '*.png' ! -name '*.zip' ! -name '*.iso' -not -path './.git/*' -exec sed -i 's/\r$//' {} +
chmod +x live/config/hooks/live/*.chroot live/config/includes.chroot/usr/bin/* live/config/includes.chroot/usr/lib/nimbus/apt-helper 2>/dev/null || true
cd live
if [ -n "${NIMBUS_LITE:-}" ]; then
  echo "Lite build: no Wine, no extra codecs/fonts/firmware (much smaller ISO; Windows apps will not run)"
  sed -i '/^wine/d;/^winetricks/d;/^cabextract/d;/^gstreamer/d;/^xfce4-goodies/d;/^fonts-noto/d;/^firmware-/d' config/package-lists/nimbus.list.chroot
  rm -f config/hooks/live/0100-wine32.hook.chroot
fi
lb config noauto \
  --distribution bookworm --architectures amd64 \
  --archive-areas "main contrib non-free-firmware" \
  --binary-images iso-hybrid --debian-installer live \
  --iso-application "Nimbus OS" --iso-publisher "Nimbus OS" --iso-volume "NIMBUS" \
  --bootappend-live "boot=live components quiet splash hostname=nimbus username=nimbus"
sudo lb build
ls -lh *.iso
