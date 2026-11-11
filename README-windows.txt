BUILDING THE NIMBUS OS LINUX ISO ON WINDOWS (NO WSL)

build.sh itself needs Linux (chroot, mounts), so on Windows the build runs inside a Linux container.

OPTION A - Docker Desktop (easiest)
 1. Install Docker Desktop (free for personal use). In Settings > General you can turn OFF "Use the WSL 2 based
    engine" (needs Windows 10/11 Pro, Enterprise or Education; it then uses Hyper-V). On Windows Home, Docker
    Desktop needs WSL 2 in the background - if you do not want that, use Option B.
 2. In Docker Desktop > Settings > Resources, give it 4 GB RAM or more and at least 30 GB of disk.
 3. Unzip nimbus-linux-edition.zip. In the folder "nl", double-click  build-windows.bat
    (for a smaller ISO without Wine, open a Command Prompt in that folder and run:  build-windows.bat -Lite )
 4. Wait 30-90 minutes with the window open. The ISO appears in the same folder as nimbus-os-linux.iso.

OPTION B - A Debian virtual machine (no Docker, no WSL)
 1. Install VirtualBox, make a Debian 12 VM (4 GB RAM, 40 GB disk, 2+ CPUs) and install Debian from the netinst ISO.
 2. Copy nimbus-linux-edition.zip into the VM (shared folder, or: python -m http.server on Windows and wget in the VM).
 3. In the VM:  sudo apt install unzip sudo ; unzip nimbus-linux-edition.zip ; cd nl ; ./build.sh
    Copy the ISO out of the VM.

OPTION C - GitHub Actions: see the main README (no software needed on your computer).

If something fails, send the last 20 lines of the output to whoever is helping you.
