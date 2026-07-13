#!/bin/bash
set -e
echo "=== Construyendo SnapLinux MP3 .deb ==="
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$ROOT_DIR/packaging/snaplinux-mp3"
mkdir -p "$PKG_DIR/opt/snaplinux"
cp "$ROOT_DIR/src/snaplinux.py" "$PKG_DIR/opt/snaplinux/snaplinux.py"
chmod +x "$PKG_DIR/opt/snaplinux/snaplinux.py"
chmod 755 "$PKG_DIR/DEBIAN/postinst"
chmod 644 "$PKG_DIR/DEBIAN/control"
dpkg-deb --build --root-owner-group "$PKG_DIR" "$ROOT_DIR/snaplinux-mp3_2.3-1_all.deb"
echo ""
echo "Listo: snaplinux-mp3_2.3-1_all.deb"
echo "Instálalo con: sudo apt install ./snaplinux-mp3_2.3-1_all.deb"
