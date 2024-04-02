WIN_PY=~/.wine/drive_c/users/kpm/AppData/Local/Programs/Python/Python311/python.exe
WIN_PYINSTALLER=~/.wine/drive_c/users/kpm/AppData/Local/Programs/Python/Python311/Scripts/pyinstaller.exe

PIFLAGS=-F -w -i ./icon.ico --collect-data sv_ttk --collect-data requests \
    --collect-data bs4

.PHONY: all build wine-install-deps wine-run pubcpy clean

all: dist/pmc-gui.exe dist/pmc-gui
build: all
wine-install-deps:
	wine $(WIN_PY) -m pip install -r requirements.txt
wine-run:
	wine $(WIN_PY) pmc-gui.py
dist/pmc-gui.exe:
	wine $(WIN_PYINSTALLER) $(PIFLAGS) ./pmc-gui.py
dist/pmc-gui:
	pyinstaller $(PIFLAGS) ./pmc-gui.py
pubcpy: all
	[ `whoami` = 'kpm' ] || exit 1
	cp dist/pmc-gui.exe .
	cp dist/pmc-gui pmc-gui-linux-x86-64
	yes | pubcpy pmc-gui.exe
	yes | pubcpy pmc-gui-linux-x86-64
	rm -f ./pmc-gui.exe
	rm -f ./pmc-gui-linux-x86-64
clean:
	rm -fr build dist pmc-gui.spec
