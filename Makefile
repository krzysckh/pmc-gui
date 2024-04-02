WIN_PY=~/.wine/drive_c/users/kpm/AppData/Local/Programs/Python/Python311/python.exe
WIN_PY_OLD=~/.wine/drive_c/users/kpm/AppData/Local/Programs/Python/Python38-32/python.exe
WIN_PYINSTALLER=~/.wine/drive_c/users/kpm/AppData/Local/Programs/Python/Python311/Scripts/pyinstaller.exe
WIN_PYINSTALLER_OLD=~/.wine/drive_c/users/kpm/AppData/Local/Programs/Python/Python38-32/Scripts/pyinstaller.exe

PIFLAGS=-F -w -i ./icon.ico --collect-data sv_ttk --collect-data requests \
    --collect-data bs4 --collect-data json

.PHONY: all build wine-install-deps wine-run pubcpy clean

all: dist/pmc-gui.exe dist/pmc-gui dist/pmc-gui-winlegacy.exe
build: all
wine-install-deps:
	wine $(WIN_PY) -m pip install -r requirements.txt
	wine $(WIN_PY_OLD) -m pip install -r requirements.txt
wine-run:
	wine $(WIN_PY_OLD) pmc-gui.py
dist/pmc-gui.exe: wine-install-deps
	wine $(WIN_PYINSTALLER) $(PIFLAGS) --add-binary "icon.ico;." ./pmc-gui.py
dist/pmc-gui-winlegacy.exe: wine-install-deps
	winetricks -q win7
	wine $(WIN_PYINSTALLER_OLD) $(PIFLAGS) --add-binary "icon.ico;." -n pmc-gui-winlegacy ./pmc-gui.py
	winetricks -q win10
dist/pmc-gui:
	pyinstaller $(PIFLAGS) -n pmc-gui-linux-x86-64 ./pmc-gui.py
pubcpy:
	[ `whoami` = 'kpm' ] || exit 1
	cd dist && sh -c 'for f in *; do yes | pubcpy $$f; done'
clean:
	rm -fr build dist pmc-gui.spec
