win-pyinstaller=~/.wine/drive_c/users/krzych/AppData/Local/Programs/Python/Python311/Scripts/pyinstaller.exe

all: dist/pmc-gui.exe
dist/pmc-gui.exe:
	wine $(win-pyinstaller) -F -w -i ./icon.ico --collect-data sv_ttk \
    ./pmc-gui.py
clean:
	rm -fr build dist pmc-gui.spec
