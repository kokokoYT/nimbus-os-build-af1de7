# Nimbus OS (Linux edition) - build the ISO on Windows, no WSL needed.
# Runs the normal build.sh inside a Debian 12 Linux container using Docker Desktop.
# Usage: double-click build-windows.bat   (add -Lite for a smaller ISO without Wine)
param([switch]$Lite)
$ErrorActionPreference = "Continue"
$proj = $PSScriptRoot
$name = "nimbus-build"

function Fail($msg) {
    Write-Host ""
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

Write-Host "=== Nimbus OS (Linux edition) - Windows builder ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail "Docker was not found. Install Docker Desktop (free for personal use) from docker.com, restart Windows, start it, then run this again. See README-windows.txt."
}
$os = (docker version --format '{{.Server.Os}}' 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    Fail "Docker is installed but not running. Start Docker Desktop, wait until it says it is running, then run this again."
}
if ($os -ne "linux") {
    Fail "Docker is set to Windows containers. Right-click the Docker icon in the system tray and choose 'Switch to Linux containers', then run this again."
}

Write-Host "[1/5] Starting a Debian 12 build container..."
docker rm -f $name 2>&1 | Out-Null
docker run -d --name $name --privileged debian:bookworm sleep infinity | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Could not start the container. Check your internet connection and that Docker has enough memory (4 GB or more)." }

Write-Host "[2/5] Copying the project into the container..."
docker exec $name mkdir -p /work | Out-Null
docker cp "$proj\." "${name}:/work"
if ($LASTEXITCODE -ne 0) { Fail "Could not copy the project into the container." }

$inner = @'
#!/bin/bash
set -e
cd /work
# Windows may have added CRLF line endings: strip them from text files
find . -type f ! -name '*.png' ! -name '*.zip' ! -name '*.iso' -exec sed -i 's/\r$//' {} +
chmod +x build.sh live/config/hooks/live/*.chroot live/config/includes.chroot/usr/bin/* \
  live/config/includes.chroot/usr/lib/nimbus/apt-helper shell/* store/* browser/perari 2>/dev/null || true
apt-get update
apt-get install -y sudo ca-certificates
bash build.sh
'@
$tmp = Join-Path $env:TEMP "nimbus-inner.sh"
[System.IO.File]::WriteAllText($tmp, ($inner -replace "`r`n", "`n"))
docker cp $tmp "${name}:/work/_inner.sh" | Out-Null
Remove-Item $tmp -ErrorAction SilentlyContinue

$liteValue = ""
if ($Lite) { $liteValue = "1"; Write-Host "Lite build selected (no Wine, smaller ISO)." }

Write-Host "[3/5] Installing the build tools and building the ISO."
Write-Host "[4/5] This takes about 30-90 minutes. Keep this window open and the computer awake." -ForegroundColor Yellow
docker exec -e "NIMBUS_LITE=$liteValue" $name bash /work/_inner.sh
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "The build failed. Scroll up to see the error and send the last 20 lines to Claude." -ForegroundColor Red
    Write-Host "The build container was kept so you can look around. When you are done, remove it with:  docker rm -f $name" -ForegroundColor Yellow
    exit 1
}

Write-Host "[5/5] Copying the finished ISO to this folder..."
$out = Join-Path $proj "nimbus-os-linux.iso"
docker cp "${name}:/work/live/live-image-amd64.hybrid.iso" $out
if ($LASTEXITCODE -ne 0) { Fail "The build finished but the ISO could not be copied out. Try: docker cp ${name}:/work/live/live-image-amd64.hybrid.iso ." }
docker rm -f $name 2>&1 | Out-Null

$mb = [math]::Round((Get-Item $out).Length / 1MB)
Write-Host ""
Write-Host "Done! ISO saved as: $out  ($mb MB)" -ForegroundColor Green
Write-Host "Write it to a USB stick with Rufus (choose 'DD Image' mode) or balenaEtcher, or run it in VirtualBox."
Start-Process explorer.exe "/select,`"$out`""
