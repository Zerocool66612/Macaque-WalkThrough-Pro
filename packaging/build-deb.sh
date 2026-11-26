#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -c 'import ast; ast.parse(open("walkthrough.py").read())'
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
chmod 755 "$root"
install -d "$root/DEBIAN" "$root/usr/bin" "$root/usr/share/macaque-walkthrough-pro" "$root/usr/share/applications" "$root/usr/share/icons/hicolor/scalable/apps"
install -m644 walkthrough.py "$root/usr/share/macaque-walkthrough-pro/"
install -m755 packaging/macaque-walkthrough-pro "$root/usr/bin/"
install -m644 packaging/macaque-walkthrough-pro.desktop "$root/usr/share/applications/"
install -m644 packaging/macaque-walkthrough-pro.svg "$root/usr/share/icons/hicolor/scalable/apps/"
install -m644 packaging/control "$root/DEBIAN/control"
mkdir -p dist
dpkg-deb --root-owner-group --build "$root" dist/macaque-walkthrough-pro_0.2-1_all.deb
