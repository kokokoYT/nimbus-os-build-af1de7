# Nimbus OS - Linux edition (Debian + Wine + Nimbus Store)

The hand-written Nimbus OS in the other ISO has no Linux kernel, so it cannot run Debian or Windows apps.
This edition is built on Debian instead, and adds:

* **Wine** (runs many Windows apps) with Wine32 and winetricks
* **Nimbus Store** (`store/nimbus-store`) - an app store: Debian packages are installed with apt, Windows apps
  are downloaded from your server, checked against a SHA-256 hash, and run through Wine
* **Catalog server** (`server/nimbus_server.py`) - hosts the app list and the Windows installers
* An installer: the ISO boots a live desktop and has Debian's "Install" entry in its boot menu

## 1. Build the ISO (needs a Debian 12 / Ubuntu PC, internet, ~15 GB free, 20-40 min)
    ./build.sh
Result: `live/live-image-amd64.hybrid.iso`. Boot it in a VM (UEFI or BIOS) or write it to a USB stick.

## 2. Run the app server
    cd server
    python3 nimbus_server.py serve --port 8080
Add apps:
    python3 nimbus_server.py add-deb --id gimp --name GIMP --package gimp --desc "Image editor" --category Graphics
    python3 nimbus_server.py add-windows setup.exe --id myapp --name "My App" --args "/S" --launch 'C:\Program Files\My App\app.exe'
    python3 nimbus_server.py add-windows tool.exe --id tool --name Tool --portable
`data/catalog.json` already lists 12 Debian apps.

## 3. Point the OS at the server
In the live system edit `/etc/nimbus/store.json` (or `~/.config/nimbus/store.json`):
    { "server": "http://YOUR-SERVER:8080" }
Then open **Nimbus Store** from the menu (or `nimbus-store list | install ID | remove ID | launch ID`).
Debian installs ask for the live password (`live`).

## Building on Windows without WSL
Double-click `build-windows.bat` (needs Docker Desktop; see `README-windows.txt` for the options, including a plain
VirtualBox VM that needs no Docker at all). It runs this same build inside a Linux container. Not tested on Windows.

## Building in the cloud (no Linux computer needed): GitHub Actions
1. Make a PUBLIC GitHub repository (free accounts have a tiny storage limit for private ones).
2. Upload `nimbus-linux-edition.zip` to the repository root (Add file > Upload files).
3. Create the file `.github/workflows/build-iso.yml` (Add file > Create new file) and paste in `build-iso.yml`.
4. Open the Actions tab > "Build Nimbus OS ISO" > Run workflow. Leave "Lite build" ticked for a smaller ISO
   (no Wine, so Windows apps will not run); untick it for the full version.
5. When it finishes (30-60 minutes) download the artifact `nimbus-os-linux-iso` from the run page.
Run it in an emulator such as Limbo (QEMU): 2 GB RAM, CD-ROM = the ISO, boot from CD-ROM, network = user mode,
mouse = usb tablet, VGA = std. Without KVM an emulated PC is slow: expect minutes to boot.

## The macOS-style desktop (menu bar + floating dock)
* `shell/nimbus-menubar` - top bar. Left: the Nimbus logo menu (About Nimbus OS, System Settings, Nimbus Store,
  Force Quit, Sleep / Restart / Shut Down, Log Out), then the active app's name in bold and File / Edit / View /
  Window / Help menus (they send standard shortcuts to the active app and control its window). Right: search,
  Wi-Fi, volume, battery and the clock (click it for a calendar).
* `shell/nimbus-dock` - floating glass dock with icon magnification, running-app dots, launch bounce and Trash.
  Edit the icons in `/etc/nimbus/dock.json` or `~/.config/nimbus/dock.json` (list of .desktop file names).
* `shell/nimbus-shell` starts both at login and sets the wallpaper. If either fails to start it falls back to a
  plain XFCE panel / Plank, so you are never left without a bar or dock.
* Look: Arc theme, Papirus icons, Cantarell font, window buttons on the left (xfwm4 `button_layout`).
  The stock XFCE panel is removed in `etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml`.
* The colored "traffic light" buttons in `desktop-preview.png` are illustrative - the build uses the Arc theme's
  buttons. The dock's glass effect needs a compositor (xfwm4's is on by default; in a VM turn on 3D/accelerated
  graphics if the dock looks solid black).
* This GTK code could not be run in the sandbox it was written in (no GTK there) - only syntax-checked and
  smoke-tested against a stub. Expect to fix small things on first boot; run `nimbus-menubar` or `nimbus-dock`
  from a terminal to see any errors.

## Perari web browser (Linux edition)
`browser/perari` is a real browser built on WebKitGTK: tabs, a search-or-address bar (words you type become a
DuckDuckGo search), downloads to ~/Downloads, find in page, zoom, full screen, saved cookies, and it runs JavaScript
and https sites. It is the first icon in the dock and the default browser for links. Firefox ESR is still installed
as a backup.
* Shortcuts: Ctrl+T new tab, Ctrl+W close tab, Ctrl+L address bar, Ctrl+R / F5 reload, Alt+Left / Alt+Right back and
  forward, Ctrl+Tab next tab, Ctrl+F find, Ctrl +/-/0 zoom, F11 full screen.
* In a virtual machine it automatically uses software rendering (no GPU needed). If pages look blank or it crashes,
  start it from a terminal with `perari` to see messages. To force GPU drawing: `PERARI_GPU=1 perari`.
* Video sites (YouTube etc.) need the gstreamer packages that are in the package list; playback in a VM can be slow.
* Like the desktop code, this could not be run where it was written (no GTK/WebKit there): the address-bar logic was
  unit-tested and the rest smoke-tested against a stub, so expect small fixes on first run.

## Installing on a real computer
1. Build the ISO (step 1 above). It is a hybrid ISO, so it can be written straight to a USB stick (8 GB or more) with
   balenaEtcher, Rufus (choose "DD Image" mode) or `sudo dd if=live-image-amd64.hybrid.iso of=/dev/sdX bs=4M status=progress`.
2. Boot the USB (BIOS or UEFI; turn Secure Boot off if it will not start). Try the live desktop first - nothing is
   changed on the computer until you choose Install in the boot menu.
3. The installer is Debian's. It can install next to another system or erase the disk - read each screen, and back up
   anything important first. Wi-Fi firmware for common Intel, Realtek, Atheros and Broadcom chips is included.
Not tested on real hardware: try it in a virtual machine or from the live USB before installing for good.

## Welcome screen (first run)
`shell/nimbus-welcome` opens on first login and walks through: connect to the internet (it checks the connection and
opens Network settings), see whether this is a virtual machine or a real computer (VMs get an optional "lighter effects"
switch), then pick dark mode and an accent color (applied live). Reopen it any time from the logo menu > Welcome to Nimbus OS.
Settings are saved in ~/.config/nimbus/theme.json; the menu bar and dock follow them. The accent color is applied through
a GTK style override on top of the Arc theme, so a few Arc details (like the window title-bar buttons) keep their default blue.

## Notes
* Not every Windows app works in Wine - check winehq.org's app database.
* Only host software you have the right to distribute. Wine apps are NOT sandboxed: use HTTPS and a server you
  trust. The store refuses downloads whose SHA-256 does not match the catalog, but a hacked server could change both.
* Test the store without installing anything: `NIMBUS_DRY_RUN=1 NIMBUS_SERVER=http://localhost:8080 ./store/nimbus-store install gimp`
