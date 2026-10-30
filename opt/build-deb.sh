#!/bin/sh

set -xe

[ -d pmc-gui ] && rm -r pmc-gui

mkdir pmc-gui
mkdir -p pmc-gui/data/usr/share/applications
mkdir -p pmc-gui/data/usr/bin
mkdir -p pmc-gui/data/usr/share/pixmaps

mkdir -p pmc-gui/control

cp pmc-gui.desktop pmc-gui/data/usr/share/applications
cp "$1" pmc-gui/data/usr/bin/pmc-gui
convert ../icon.ico pmc-gui/data/usr/share/pixmaps/pmc-gui.png

( cd pmc-gui/data && find . -type f -exec md5sum '{}' ';' ) > pmc-gui/control/md5sums
cp control pmc-gui/control/control

( cd pmc-gui/data && tar cvzf ../data.tar.gz . )
( cd pmc-gui/control && tar cvzf ../control.tar.gz . )
echo "2.0" > pmc-gui/debian-binary
rm -r pmc-gui/data
rm -r pmc-gui/control

[ -f pmc-gui.deb ] && rm pmc-gui.deb
ar r pmc-gui.deb pmc-gui/debian-binary
ar r pmc-gui.deb pmc-gui/control.tar.gz
ar r pmc-gui.deb pmc-gui/data.tar.gz
